"""
OpenRouter API integration for AI-powered data analysis
Converts HTML profiles to markdown insights
"""
from openai import OpenAI
from app.config.settings import settings
from app.utils.logger import logger


# Lazy initialization of OpenRouter client (configure on first use)
_openrouter_client = None


def _get_openrouter_client():
    """Get or initialize OpenRouter client on first use"""
    global _openrouter_client
    if _openrouter_client is None:
        try:
            _openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key
            )
            logger.info("OpenRouter API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter API: {str(e)}")
            raise
    return _openrouter_client



def analyze_profile_with_gemini(summary_stats: dict, profile_type: str = "raw") -> str:
    """
    Analyze profile summary statistics and generate markdown insights
    
    Args:
        summary_stats: Dictionary with profile statistics
        profile_type: "raw" or "clean" profile
    
    Returns:
        Markdown formatted analysis from AI
    """
    try:
        import json
        
        client = _get_openrouter_client()
        
        logger.info(f"Sending {profile_type} profile to OpenRouter API for analysis")
        
        # Convert stats to readable text format
        stats_text = f"""
Dataset Statistics:
- Total Rows: {summary_stats['total_rows']}
- Total Columns: {summary_stats['total_columns']}
- Total Cells: {summary_stats['total_cells']}
- Duplicate Rows: {summary_stats['duplicate_rows']}

Columns: {', '.join(summary_stats['columns'])}

Data Types:
{json.dumps(summary_stats['dtypes'], indent=2)}

Missing Values (count):
{json.dumps(summary_stats['missing_values'], indent=2)}

Missing Values (percentage):
{json.dumps(summary_stats['missing_percentage'], indent=2)}

Numeric Columns: {', '.join(summary_stats['numeric_columns'])}
Categorical Columns: {', '.join(summary_stats['categorical_columns'])}
"""
        
        prompt = f"""
You are a data quality analyst. Analyze the following dataset statistics and provide a comprehensive markdown summary.

Profile Type: {profile_type.upper()} Data

{stats_text}

Please provide your analysis in markdown format with the following sections:
1. **Executive Summary** - Brief overview of the dataset
2. **Data Quality Assessment** - Missing values, completeness score, data types
3. **Column Insights** - Key observations about each column
4. **Potential Issues** - Data quality problems, anomalies, outliers
5. **Statistical Summary** - Key statistics and distributions
6. **Recommendations** - Actions to improve data quality

Format your response in clean markdown with headers, bullet points, and code blocks where appropriate.
"""
        
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        markdown_analysis = response.choices[0].message.content
        logger.info(f"OpenRouter analysis completed for {profile_type} profile")
        
        return markdown_analysis
    
    except Exception as e:
        logger.error(f"Error analyzing profile with OpenRouter: {str(e)}")
        raise


def save_markdown_report(markdown_content: str, job_id: str, profile_type: str = "raw") -> str:
    """
    Save markdown analysis to file
    
    Args:
        markdown_content: Markdown formatted analysis
        job_id: Job identifier
        profile_type: "raw" or "clean"
    
    Returns:
        Path to saved markdown file
    """
    try:
        import os
        report_dir = "storage/reports"
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, f"{job_id}_{profile_type}_profile.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown report saved: {report_path}")
        return report_path
    
    except Exception as e:
        logger.error(f"Error saving markdown report: {str(e)}")
        raise


async def analyze_profile_async(summary_stats: dict, job_id: str, profile_type: str = "raw") -> dict:
    """
    Async wrapper for profile analysis
    
    Args:
        summary_stats: Dictionary with profile statistics
        job_id: Job identifier
        profile_type: "raw" or "clean"
    
    Returns:
        Dictionary with analysis and file path
    """
    try:
        # Get markdown analysis from AI
        markdown_analysis = analyze_profile_with_gemini(summary_stats, profile_type)
        
        # Save markdown report
        report_path = save_markdown_report(markdown_analysis, job_id, profile_type)
        
        return {
            "status": "success",
            "report_path": report_path,
            "analysis": markdown_analysis
        }
    
    except Exception as e:
        logger.error(f"Error in async profile analysis: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }
