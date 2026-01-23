"""
Data export and reporting functionality.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Union
import pandas as pd

from models import EnrichedProperty, ZillowProperty
from config import config
from utils.logger import logger


class DataExporter:
    """Exports property data to various formats."""
    
    def __init__(self):
        self.output_dir = Path(config.output.output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def _generate_filename(self, format: str, prefix: str = "properties") -> str:
        """Generate timestamped filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{format}"
    
    def _prepare_dataframe(self, properties: List[Union[ZillowProperty, EnrichedProperty]]) -> pd.DataFrame:
        """Convert property list to DataFrame."""
        data = []
        
        for prop in properties:
            # Check if it's an EnrichedProperty or just ZillowProperty
            is_enriched = isinstance(prop, EnrichedProperty)
            zillow_data = prop.zillow_data if is_enriched else prop
            
            row = {
                # Zillow data
                'Address': str(zillow_data.address),
                'Street': zillow_data.address.street,
                'Borough': zillow_data.address.borough,
                'Price': zillow_data.price,
                'Bedrooms': zillow_data.bedrooms,
                'Bathrooms': zillow_data.bathrooms,
                'Square Feet': zillow_data.square_feet,
                'Property Type': zillow_data.property_type,
                'Listing Status': zillow_data.listing_status,
                'Zillow URL': zillow_data.url,
                'ZPID': zillow_data.zpid,
                'Scraped At': zillow_data.scraped_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Add HPD data only for EnrichedProperty
            if is_enriched:
                row.update({
                    # HPD data
                    'HPD Match': 'Yes' if prop.hpd_match_found else 'No',
                    'Match Confidence': str(prop.match_confidence) if prop.match_confidence else 'N/A',
                    'Total Units': int(prop.total_units) if prop.hpd_match_found and prop.total_units else 'N/A',
                    'Has B Units': 'Yes' if prop.has_b_units else 'No',
                    'B Unit Count': int(prop.b_unit_count) if prop.has_b_units else 0,
                    'Building ID': str(prop.hpd_data.building_id) if prop.hpd_data and prop.hpd_data.building_id else 'N/A',
                    'Processed At': prop.processed_at.strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # Add B unit details
                if prop.hpd_data and prop.has_b_units:
                    try:
                        b_unit_numbers = [str(unit.unit_number) for unit in prop.hpd_data.b_units if unit.unit_number]
                        row['B Unit Numbers'] = ', '.join(b_unit_numbers) if b_unit_numbers else 'N/A'
                    except Exception as e:
                        logger.warning(f"Error extracting B unit numbers: {e}")
                        row['B Unit Numbers'] = 'N/A'
                else:
                    row['B Unit Numbers'] = 'N/A'
            
            # Safety check: ensure no complex objects in row values
            for key, value in list(row.items()):
                if isinstance(value, (list, dict, tuple)):
                    row[key] = str(value)
                elif value is not None and hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool)):
                    row[key] = str(value)
            
            data.append(row)
        
        # Create DataFrame and aggressively clean it
        df = pd.DataFrame(data)
        
        # Ensure all column names are valid strings without special characters
        df.columns = [str(col).replace('[', '').replace(']', '').replace('{', '').replace('}', '') for col in df.columns]
        
        # Convert all values to safe types
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict, tuple, set)) else x)
        
        return df
    
    def export_to_csv(self, properties: List[EnrichedProperty], prefix: str = "properties") -> str:
        """
        Export properties to CSV.
        
        Args:
            properties: List of EnrichedProperty objects
            prefix: Filename prefix
            
        Returns:
            Path to exported file
        """
        df = self._prepare_dataframe(properties)
        filename = self._generate_filename('csv', prefix)
        filepath = self.output_dir / filename
        
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(properties)} properties to CSV: {filepath}")
        
        return str(filepath)
    
    def export_to_excel(self, properties: List[EnrichedProperty], prefix: str = "properties") -> str:
        """
        Export properties to Excel with formatting.
        
        Args:
            properties: List of EnrichedProperty objects
            prefix: Filename prefix
            
        Returns:
            Path to exported file
        """
        df = self._prepare_dataframe(properties)
        filename = self._generate_filename('xlsx', prefix)
        filepath = self.output_dir / filename
        
        # Debug: Check for problematic columns/values
        logger.debug(f"DataFrame columns: {list(df.columns)}")
        logger.debug(f"DataFrame shape: {df.shape}")
        
        # Extra safety: ensure all column names are simple strings
        df.columns = [str(c).strip() for c in df.columns]
        
        # Use xlsxwriter engine instead of openpyxl - it's more forgiving
        try:
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Properties')
                
                # Get workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Properties']
                
                # Add some basic formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#D3D3D3',
                    'border': 1
                })
                
                # Write headers with formatting
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-fit columns
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.set_column(i, i, min(column_len, 50))
                    
        except ImportError:
            # Fallback to openpyxl if xlsxwriter not available
            logger.warning("xlsxwriter not available, falling back to openpyxl")
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Properties')
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Properties']
                
                # Auto-adjust column widths
                for column in df:
                    column_length = max(df[column].astype(str).map(len).max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_length + 2, 50)
        
        logger.info(f"Exported {len(properties)} properties to Excel: {filepath}")
        
        return str(filepath)
    
    def export_to_json(self, properties: List[EnrichedProperty], prefix: str = "properties") -> str:
        """
        Export properties to JSON.
        
        Args:
            properties: List of EnrichedProperty objects
            prefix: Filename prefix
            
        Returns:
            Path to exported file
        """
        filename = self._generate_filename('json', prefix)
        filepath = self.output_dir / filename
        
        # Convert to dict
        data = [prop.model_dump(mode='json') for prop in properties]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Exported {len(properties)} properties to JSON: {filepath}")
        
        return str(filepath)
    
    def generate_summary_report(self, properties: List[EnrichedProperty], prefix: str = "properties") -> str:
        """
        Generate a summary report.
        
        Args:
            properties: List of EnrichedProperty objects
            prefix: Filename prefix
            
        Returns:
            Path to report file
        """
        filename = f"{prefix}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = self.output_dir / filename
        
        # Check if properties are EnrichedProperty or just ZillowProperty
        # Check the first item to determine type
        is_enriched = isinstance(properties[0], EnrichedProperty) if properties else False
        
        # Calculate statistics
        total_properties = len(properties)
        
        if is_enriched:
            # Full statistics for EnrichedProperty
            with_hpd_match = sum(1 for p in properties if p.hpd_match_found)
            with_b_units = sum(1 for p in properties if p.has_b_units)
            meets_criteria = sum(1 for p in properties if p.meets_criteria)
            
            zillow_data = [p.zillow_data for p in properties]
            avg_price = sum(p.price for p in zillow_data if p.price) / total_properties if total_properties > 0 else 0
            avg_units = sum(p.total_units for p in properties if p.total_units > 0) / with_hpd_match if with_hpd_match > 0 else 0
            total_b_units = sum(p.b_unit_count for p in properties)
            
            # Get top properties
            top_properties = sorted(
                [p for p in properties if p.meets_criteria],
                key=lambda p: float(p.notes.split(': ')[1].split('/')[0]) if p.notes else 0,
                reverse=True
            )[:10]
        else:
            # Basic statistics for ZillowProperty
            with_hpd_match = 0
            with_b_units = 0
            meets_criteria = 0
            avg_price = sum(p.price for p in properties if p.price) / total_properties if total_properties > 0 else 0
            avg_units = 0
            total_b_units = 0
            top_properties = []
        
        # Write report
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("REAL ESTATE PROPERTY ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Properties Analyzed:      {total_properties}\n")
            
            if is_enriched:
                f.write(f"Properties with HPD Match:      {with_hpd_match} ({with_hpd_match/total_properties*100:.1f}%)\n")
                f.write(f"Properties with B Units:        {with_b_units} ({with_b_units/total_properties*100:.1f}%)\n")
                f.write(f"Properties Meeting Criteria:    {meets_criteria} ({meets_criteria/total_properties*100:.1f}%)\n")
                f.write(f"Total B Units Found:            {total_b_units}\n")
                f.write(f"Average Units per Building:     {avg_units:.1f}\n")
            
            f.write(f"Average Listing Price:          ${avg_price:,.0f}\n\n")
            
            if is_enriched and top_properties:
                f.write("TOP 10 INVESTMENT OPPORTUNITIES\n")
                f.write("-" * 80 + "\n\n")
                
                for i, prop in enumerate(top_properties, 1):
                    score = prop.notes.split(': ')[1].split('/')[0] if prop.notes else '0'
                    f.write(f"{i}. {prop.zillow_data.address.street}\n")
                    f.write(f"   Price: ${prop.zillow_data.price:,.0f} | ")
                    f.write(f"Units: {prop.total_units} | ")
                    f.write(f"B Units: {prop.b_unit_count} | ")
                    f.write(f"Score: {score}/100\n")
                    if prop.zillow_data.url:
                        f.write(f"   URL: {prop.zillow_data.url}\n")
                    f.write("\n")
            else:
                f.write("PROPERTY ADDRESSES\n")
                f.write("-" * 80 + "\n\n")
                for i, prop in enumerate(properties[:20], 1):  # Show first 20
                    zillow_data = prop.zillow_data if is_enriched else prop
                    f.write(f"{i}. {zillow_data.address.street}\n")
                    f.write(f"   Price: ${zillow_data.price:,.0f} | ")
                    f.write(f"Beds: {zillow_data.bedrooms} | ")
                    f.write(f"Baths: {zillow_data.bathrooms}\n")
                    if zillow_data.url:
                        f.write(f"   URL: {zillow_data.url}\n")
                    f.write("\n")
                if len(properties) > 20:
                    f.write(f"... and {len(properties) - 20} more properties\n\n")
            
            f.write("\n" + "=" * 80 + "\n")
        
        logger.info(f"Generated summary report: {filepath}")
        
        return str(filepath)
    
    def export_all_formats(self, properties: List[EnrichedProperty], filename_prefix: str = "properties") -> dict:
        """
        Export to all configured formats.
        
        Args:
            properties: List of EnrichedProperty objects
            filename_prefix: Prefix for output filenames
            
        Returns:
            Dictionary mapping format to filepath
        """
        exports = {}
        
        for format in config.output.output_formats:
            if format.lower() == 'csv':
                exports['csv'] = self.export_to_csv(properties, filename_prefix)
            elif format.lower() in ['excel', 'xlsx']:
                exports['excel'] = self.export_to_excel(properties, filename_prefix)
            elif format.lower() == 'json':
                exports['json'] = self.export_to_json(properties, filename_prefix)
        
        # Always generate summary report
        exports['report'] = self.generate_summary_report(properties, filename_prefix)
        
        return exports
