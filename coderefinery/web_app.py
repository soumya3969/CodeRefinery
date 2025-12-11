"""
Streamlit web interface for CodeRefinery.
"""
import streamlit as st
import json
import tempfile
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from coderefinery.analyzer import CodeAnalyzer
from coderefinery.models import Severity


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="CodeRefinery - AI Code Reviewer",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 CodeRefinery")
    st.markdown("**AI-Powered Code Quality Analyzer**")
    
    st.markdown("""
    Welcome to **CodeRefinery** - your automated code quality assistant! 
    Upload Python files or paste code directly to get comprehensive analysis including:
    - Style issues (PEP8/flake8)
    - Code formatting suggestions (black)
    - Complexity metrics (cyclomatic complexity)
    - Bug detection and security issues
    - Automated refactoring suggestions
    """)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        max_complexity = st.slider(
            "Max Complexity Threshold", 
            min_value=1, max_value=20, value=10,
            help="Functions with complexity above this will be flagged"
        )
        
        apply_black = st.checkbox(
            "Apply Black Formatting", 
            value=False,
            help="Automatically apply black code formatting"
        )
        
        export_formats = st.multiselect(
            "Export Formats",
            options=["markdown", "json"],
            default=["markdown"],
            help="Choose export formats for the analysis report"
        )
        
        st.header("📊 Quick Stats")
        if 'analysis_result' in st.session_state:
            result = st.session_state.analysis_result
            st.metric("Files Analyzed", result.overall_metrics.files_analyzed)
            st.metric("Total Issues", result.overall_metrics.total_issues)
            st.metric("High Severity", result.overall_metrics.high_severity)
            st.metric("Complexity Violations", result.overall_metrics.complexity_violations)
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📝 Code Input", "📊 Analysis Results", "📄 Reports"])
    
    with tab1:
        st.header("Code Input")
        
        input_method = st.radio(
            "Choose input method:",
            options=["Paste Code", "Upload Files", "JSON Input"],
            horizontal=True
        )
        
        files_data = []
        
        if input_method == "Paste Code":
            col1, col2 = st.columns([3, 1])
            
            with col1:
                code_input = st.text_area(
                    "Paste your Python code here:",
                    height=400,
                    placeholder="def hello_world():\n    print('Hello, World!')\n\n# Your code here..."
                )
                
                filename = st.text_input(
                    "Filename (optional):",
                    value="main.py",
                    help="Give your code a filename for better reporting"
                )
            
            with col2:
                if st.button("🔍 Analyze Code", type="primary", use_container_width=True):
                    if code_input.strip():
                        files_data = [{
                            "path": filename,
                            "language": "python", 
                            "content": code_input
                        }]
                    else:
                        st.error("Please paste some code to analyze!")
        
        elif input_method == "Upload Files":
            uploaded_files = st.file_uploader(
                "Choose Python files",
                type=['py'],
                accept_multiple_files=True,
                help="Upload one or more .py files for analysis"
            )
            
            if uploaded_files:
                st.success(f"Uploaded {len(uploaded_files)} file(s)")
                
                for uploaded_file in uploaded_files:
                    st.write(f"📁 {uploaded_file.name}")
                
                if st.button("🔍 Analyze Files", type="primary"):
                    files_data = []
                    for uploaded_file in uploaded_files:
                        content = str(uploaded_file.read(), "utf-8")
                        files_data.append({
                            "path": uploaded_file.name,
                            "language": "python",
                            "content": content
                        })
        
        elif input_method == "JSON Input":
            st.markdown("**JSON Format Example:**")
            st.code('''
{
  "files": [
    {"path": "app.py", "language": "python", "content": "def foo():\\n    print('hi')"},
    {"path": "utils.py", "language": "python", "content": "def add(a,b):return a+b"}
  ],
  "options": {
    "apply_black": false,
    "max_complexity_threshold": 10,
    "export_formats": ["markdown","json"]
  }
}
            ''', language="json")
            
            json_input = st.text_area(
                "Paste JSON input:",
                height=300,
                placeholder="Paste your JSON configuration here..."
            )
            
            if st.button("🔍 Analyze JSON", type="primary"):
                try:
                    data = json.loads(json_input)
                    files_data = data.get('files', [])
                    
                    # Override options from JSON
                    options = data.get('options', {})
                    if 'max_complexity_threshold' in options:
                        max_complexity = options['max_complexity_threshold']
                    if 'apply_black' in options:
                        apply_black = options['apply_black']
                    if 'export_formats' in options:
                        export_formats = options['export_formats']
                        
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")
                    files_data = []
        
        # Perform analysis if files_data is populated
        if files_data:
            with st.spinner("Analyzing code..."):
                options = {
                    "max_complexity_threshold": max_complexity,
                    "apply_black": apply_black,
                    "export_formats": export_formats
                }
                
                analyzer = CodeAnalyzer(max_complexity_threshold=max_complexity)
                result = analyzer.analyze_files(files_data, options)
                st.session_state.analysis_result = result
                
                st.success("✅ Analysis complete!")
                st.balloons()
    
    with tab2:
        st.header("Analysis Results")
        
        if 'analysis_result' not in st.session_state:
            st.info("👆 Please analyze some code in the 'Code Input' tab first!")
            return
        
        result = st.session_state.analysis_result
        
        # Summary
        st.subheader("📋 Summary")
        st.info(result.summary)
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Files", result.overall_metrics.files_analyzed)
        with col2:
            st.metric("Total Issues", result.overall_metrics.total_issues)
        with col3:
            st.metric("High Severity", result.overall_metrics.high_severity)
        with col4:
            st.metric("Complexity Issues", result.overall_metrics.complexity_violations)
        
        # Tool status
        if result.tool_status != "all tools available":
            st.warning(f"⚠️ {result.tool_status}")
        
        # File-by-file analysis
        st.subheader("📁 File Analysis")
        
        for i, file_analysis in enumerate(result.files):
            with st.expander(f"📄 {file_analysis.path}", expanded=True):
                
                # Create tabs for different issue types
                file_tabs = st.tabs(["🎨 Style Issues", "🐛 Bugs", "📊 Complexity", "🔧 Code Changes"])
                
                with file_tabs[0]:  # Style Issues
                    if file_analysis.style_issues:
                        for issue in file_analysis.style_issues:
                            severity_color = {
                                Severity.HIGH: "🔴",
                                Severity.MEDIUM: "🟡", 
                                Severity.LOW: "🟢"
                            }.get(issue.severity, "⚪")
                            
                            st.markdown(f"""
                            **Line {issue.line}** {severity_color} `{issue.code}`  
                            {issue.message}  
                            💡 *Suggestion: {issue.suggestion}*
                            """)
                    else:
                        st.success("✅ No style issues found!")
                
                with file_tabs[1]:  # Bugs
                    if file_analysis.bugs:
                        for bug in file_analysis.bugs:
                            severity_icon = {
                                Severity.HIGH: "🚨",
                                Severity.MEDIUM: "⚠️",
                                Severity.LOW: "ℹ️"
                            }.get(bug.severity, "❓")
                            
                            st.markdown(f"""
                            **Line {bug.line}** {severity_icon} `{bug.severity.value.upper()}`  
                            {bug.message}
                            """)
                    else:
                        st.success("✅ No bugs detected!")
                
                with file_tabs[2]:  # Complexity
                    complexity_metrics = file_analysis.complexity.get('function_metrics', [])
                    if complexity_metrics:
                        st.markdown(f"**Average CCN:** {file_analysis.complexity.get('avg_ccn', 0):.1f}")
                        
                        for metric in complexity_metrics:
                            ccn = metric['ccn']
                            if ccn > max_complexity:
                                st.error(f"⚠️ **{metric['name']}** (line {metric['lineno']}): CCN = {ccn}")
                            elif ccn > max_complexity * 0.7:
                                st.warning(f"⚡ **{metric['name']}** (line {metric['lineno']}): CCN = {ccn}")
                            else:
                                st.success(f"✅ **{metric['name']}** (line {metric['lineno']}): CCN = {ccn}")
                    else:
                        st.info("No function complexity metrics available")
                
                with file_tabs[3]:  # Code Changes
                    if file_analysis.after_snippet != file_analysis.before_snippet:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Before:**")
                            st.code(file_analysis.before_snippet, language="python")
                        
                        with col2:
                            st.markdown("**After:**")
                            st.code(file_analysis.after_snippet, language="python")
                        
                        if file_analysis.patch:
                            st.markdown("**Unified Diff:**")
                            st.code(file_analysis.patch, language="diff")
                    else:
                        st.info("No formatting changes suggested")
    
    with tab3:
        st.header("Export Reports")
        
        if 'analysis_result' not in st.session_state:
            st.info("👆 Please analyze some code first!")
            return
        
        result = st.session_state.analysis_result
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            if "markdown" in result.export:
                st.subheader("📝 Markdown Report")
                markdown_content = result.export["markdown"]
                st.markdown(markdown_content)
                
                # Download button
                st.download_button(
                    label="📥 Download Markdown Report",
                    data=markdown_content,
                    file_name=f"coderefinery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
        
        with col2:
            if "json" in result.export:
                st.subheader("🔧 JSON Report")
                json_content = json.dumps(result.export["json"], indent=2)
                st.code(json_content, language="json")
                
                # Download button
                st.download_button(
                    label="📥 Download JSON Report",
                    data=json_content,
                    file_name=f"coderefinery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Download all reports as ZIP
        if result.export:
            st.subheader("📦 Download All Reports")
            
            # Create ZIP file
            zip_buffer = BytesIO()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                if "markdown" in result.export:
                    zip_file.writestr(
                        f"coderefinery_report_{timestamp}.md", 
                        result.export["markdown"]
                    )
                
                if "json" in result.export:
                    zip_file.writestr(
                        f"coderefinery_report_{timestamp}.json",
                        json.dumps(result.export["json"], indent=2)
                    )
            
            zip_buffer.seek(0)
            
            st.download_button(
                label="📦 Download All Reports (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"coderefinery_reports_{timestamp}.zip",
                mime="application/zip"
            )


if __name__ == "__main__":
    main()