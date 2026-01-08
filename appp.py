"""
Watermark Security Intelligence Chatbot
========================================
A RAG-based chatbot for analyzing Apache logs, detecting anomalies, 
and providing security insights for watermarking/DLP systems.

Technology Stack & Rationale:
-----------------------------
1. LangChain - Orchestrates RAG pipeline, simplifies LLM integration
2. ChromaDB - Lightweight vector database, runs in-memory (perfect for Colab)
3. Sentence-Transformers - Open-source embeddings, no API costs
4. Groq API - Free, fast inference (Llama 3 model)
5. Gradio - Interactive UI that works natively in Colab
6. Pandas - Data manipulation and analysis
7. Plotly - Interactive charts for visualizations
"""

# ============================================================================
# SECTION 1: IMPORTS
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re
import json
import os

# LangChain / Groq imports
from langchain_groq import ChatGroq

# UI
import gradio as gr

# ============================================================================
# SECTION 2: DATA PREPARATION
# ============================================================================

def create_sample_data():
   
    
    # Access Logs Sample
    access_logs = """timestamp,ip_address,method,endpoint,http_version,status_code,response_size,response_time_ms,user_agent,department,user_id
2025-01-06 08:15:23,192.168.31.45,POST,/prg/swm/web_syslog_main_select.php,HTTP/1.1,200,1847,234,Mozilla/5.0,Engineering,user_1001
2025-01-06 08:18:34,203.45.12.89,POST,/pc/html/member/do_login.html,HTTP/1.1,401,234,45,python-requests/2.28.0,Unknown,anonymous
2025-01-06 08:18:35,203.45.12.89,POST,/pc/html/member/do_login.html,HTTP/1.1,401,234,42,python-requests/2.28.0,Unknown,anonymous
2025-01-06 08:27:45,192.168.31.233,POST,/prg/swm/web_syslog_main_select.php,HTTP/1.1,500,0,3456,Mozilla/5.0,Marketing,user_5012
2025-01-06 08:31:23,203.45.12.89,GET,/admin/,HTTP/1.1,403,456,12,sqlmap/1.6.12,Unknown,anonymous
2025-01-06 08:34:23,192.168.31.201,POST,/prg/swm/web_syslog_data_select.php,HTTP/1.1,503,0,5234,Mozilla/5.0,IT,admin_001"""
    
    # Error Logs Sample
    error_logs = """timestamp,log_level,process_id,thread_id,client_ip,error_code,error_message,file_path,line_number,severity_score
2025-01-06 08:15:23,warn,11624,9276,192.168.31.45,PHP_Warning,PHP Warning: Undefined array key 'LDAP_Uri',C:\\Apache24\\htdocs\\pc\\html\\member\\do_login.html,17,5
2025-01-06 08:18:34,error,11624,8734,203.45.12.89,AUTH_FAILED,Authentication failed for user 'admin' - invalid credentials,C:\\Apache24\\htdocs\\pc\\html\\member\\do_login.html,45,7
2025-01-06 08:18:38,critical,11624,8734,203.45.12.89,BRUTE_FORCE,Brute force attack detected from IP 203.45.12.89 - 5 failed attempts in 5 seconds,C:\\Apache24\\htdocs\\pc\\html\\member\\do_login.html,0,9
2025-01-06 08:27:45,error,11624,6543,192.168.31.233,PHP_Fatal,PHP Fatal error: Uncaught mysqli_sql_exception: Too many connections,C:\\Apache24\\htdocs\\prg\\swm\\web_syslog_main_select.php,67,9
2025-01-06 08:45:32,warn,11624,2345,192.168.31.122,AGENT_KILL,Agent termination attempt detected from user_3012,C:\\Apache24\\htdocs\\prg\\swm\\web_agent_kill_attempt.php,23,6"""
    
    # Save to files
    with open('access_logs.csv', 'w') as f:
        f.write(access_logs)
    
    with open('error_logs.csv', 'w') as f:
        f.write(error_logs)
    
    return pd.read_csv('access_logs.csv'), pd.read_csv('error_logs.csv')

# ============================================================================
# SECTION 3: LOG ANALYSIS FUNCTIONS
# ============================================================================

class LogAnalyzer:
    """Analyzes logs and detects patterns/anomalies"""
    
    def __init__(self, access_df, error_df):
        self.access_df = access_df
        self.error_df = error_df
    
    def detect_security_threats(self):
        """Detect brute force, SQL injection, bot activity"""
        threats = []
        
        # Brute force detection (multiple 401s from same IP)
        failed_logins = self.access_df[self.access_df['status_code'] == 401]
        ip_failures = failed_logins.groupby('ip_address').size()
        
        for ip, count in ip_failures.items():
            if count >= 3:
                threats.append({
                    'severity': 'HIGH',
                    'type': 'Brute Force Attack',
                    'details': f'{count} failed login attempts from IP {ip}',
                    'recommendation': f'Block IP {ip} and enable rate limiting'
                })
        
        # SQL injection detection
        sql_patterns = self.access_df[
            self.access_df['user_agent'].str.contains('sqlmap|curl', case=False, na=False)
        ]
        
        if len(sql_patterns) > 0:
            for _, row in sql_patterns.iterrows():
                threats.append({
                    'severity': 'MEDIUM',
                    'type': 'SQL Injection Attempt',
                    'details': f"Suspicious tool detected: {row['user_agent']} from {row['ip_address']}",
                    'recommendation': 'Review WAF rules and input sanitization'
                })
        
        # Bot detection
        bot_traffic = self.access_df[
            self.access_df['user_agent'].str.contains('bot|python|curl', case=False, na=False)
        ]
        
        if len(bot_traffic) > 0:
            threats.append({
                'severity': 'LOW',
                'type': 'Automated Bot Activity',
                'details': f'{len(bot_traffic)} requests from automated tools',
                'recommendation': 'Implement CAPTCHA on sensitive endpoints'
            })
        
        return threats
    
    def analyze_errors(self):
        """Analyze 4xx and 5xx errors"""
        errors = []
        
        # 500 errors
        server_errors = self.access_df[self.access_df['status_code'] >= 500]
        if len(server_errors) > 0:
            for endpoint in server_errors['endpoint'].unique():
                count = len(server_errors[server_errors['endpoint'] == endpoint])
                errors.append({
                    'severity': 'HIGH',
                    'error_type': '500 Internal Server Error',
                    'endpoint': endpoint,
                    'count': count,
                    'recommendation': 'Check PHP error logs for specific cause'
                })
        
        # 404 errors
        not_found = self.access_df[self.access_df['status_code'] == 404]
        if len(not_found) > 0:
            errors.append({
                'severity': 'MEDIUM',
                'error_type': '404 Not Found',
                'count': len(not_found),
                'recommendation': 'Fix broken links or implement proper routing'
            })
        
        return errors
    
    def detect_performance_issues(self):
        """Identify slow endpoints"""
        issues = []
        
        # Find slow endpoints (>1000ms)
        slow_requests = self.access_df[self.access_df['response_time_ms'] > 1000]
        
        if len(slow_requests) > 0:
            for endpoint in slow_requests['endpoint'].unique():
                endpoint_data = slow_requests[slow_requests['endpoint'] == endpoint]
                avg_time = endpoint_data['response_time_ms'].mean()
                max_time = endpoint_data['response_time_ms'].max()
                
                issues.append({
                    'severity': 'HIGH' if max_time > 3000 else 'MEDIUM',
                    'endpoint': endpoint,
                    'avg_response_time': f'{avg_time:.0f}ms',
                    'peak_response_time': f'{max_time:.0f}ms',
                    'optimization': 'Add database indexing or implement caching'
                })
        
        return issues
    
    def generate_traffic_summary(self):
        """Generate traffic overview"""
        total_requests = len(self.access_df)
        error_rate = len(self.access_df[self.access_df['status_code'] >= 400]) / total_requests * 100
        
        top_endpoints = self.access_df['endpoint'].value_counts().head(5)
        top_ips = self.access_df['ip_address'].value_counts().head(5)
        
        return {
            'total_requests': total_requests,
            'error_rate': f'{error_rate:.1f}%',
            'top_endpoints': top_endpoints.to_dict(),
            'top_ips': top_ips.to_dict()
        }
    
    def detect_anomalies(self):
        """Detect unusual patterns"""
        anomalies = []
        
        # Check error logs for critical issues
        critical_errors = self.error_df[self.error_df['severity_score'] >= 8]
        
        for _, error in critical_errors.iterrows():
            anomalies.append({
                'type': error['error_code'],
                'severity': 'CRITICAL',
                'message': error['error_message'],
                'timestamp': error['timestamp']
            })
        
        # Agent kill attempts
        agent_kills = self.error_df[self.error_df['error_code'] == 'AGENT_KILL']
        if len(agent_kills) > 0:
            anomalies.append({
                'type': 'Suspicious Agent Activity',
                'severity': 'HIGH',
                'message': f'{len(agent_kills)} agent termination attempts detected',
                'timestamp': 'Various'
            })
        
        return anomalies

# ============================================================================
# SECTION 4: LLM + CHATBOT INTERFACE (no external vector DB)
# ============================================================================

def create_ui(analyzer, default_api_key=None):
    """Create Gradio UI"""
    
    def handle_query(query, api_key):
        """Process user query"""
        if not api_key:
            return "⚠️ Please enter your Groq API key first. Get one free at https://console.groq.com"
        
        try:
            # Handle predefined prompts
            if query == "security_threats":
                threats = analyzer.detect_security_threats()
                response = "🔐 **Security Threat Detection**\n\n"
                for threat in threats:
                    response += f"**[{threat['severity']}] {threat['type']}**\n"
                    response += f"- {threat['details']}\n"
                    response += f"- *Recommendation:* {threat['recommendation']}\n\n"
                return response
            
            elif query == "error_analysis":
                errors = analyzer.analyze_errors()
                response = "⚠️ **Error Analysis (4xx/5xx)**\n\n"
                for error in errors:
                    response += f"**[{error['severity']}] {error['error_type']}**\n"
                    response += f"- Count: {error.get('count', 'N/A')}\n"
                    response += f"- *Fix:* {error['recommendation']}\n\n"
                return response
            
            elif query == "performance_issues":
                issues = analyzer.detect_performance_issues()
                response = "⚡ **Performance Analysis**\n\n"
                for issue in issues:
                    response += f"**[{issue['severity']}] {issue['endpoint']}**\n"
                    response += f"- Avg: {issue['avg_response_time']}, Peak: {issue['peak_response_time']}\n"
                    response += f"- *Optimization:* {issue['optimization']}\n\n"
                return response
            
            elif query == "traffic_summary":
                summary = analyzer.generate_traffic_summary()
                response = "📈 **Traffic Summary**\n\n"
                response += f"- Total Requests: {summary['total_requests']}\n"
                response += f"- Error Rate: {summary['error_rate']}\n"
                response += f"\n**Top Endpoints:**\n"
                for endpoint, count in list(summary['top_endpoints'].items())[:3]:
                    response += f"- {endpoint}: {count} requests\n"
                return response
            
            elif query == "anomaly_detection":
                anomalies = analyzer.detect_anomalies()
                response = "🔎 **Anomaly Detection**\n\n"
                for anomaly in anomalies:
                    response += f"**[{anomaly['severity']}] {anomaly['type']}**\n"
                    response += f"- {anomaly['message']}\n"
                    response += f"- Time: {anomaly['timestamp']}\n\n"
                return response
            
            # Natural language query using Groq directly
            else:
                llm = ChatGroq(
                    api_key=api_key,
                    model_name="llama-3.3-70b-versatile",
                    temperature=0.1,
                )

                # Lightweight "context" built from analyzer summaries
                summary = analyzer.generate_traffic_summary()
                threats = analyzer.detect_security_threats()
                anomalies = analyzer.detect_anomalies()

                context_parts = [
                    f"Traffic summary: total_requests={summary['total_requests']}, error_rate={summary['error_rate']}.",
                    f"Top endpoints: {summary['top_endpoints']}",
                    f"Top IPs: {summary['top_ips']}",
                    f"Detected threats: {threats}",
                    f"Detected anomalies: {anomalies}",
                ]
                context_text = "\n".join(context_parts)

                prompt = f"""
You are an AI security analyst for a watermarking and DLP (Data Leak Prevention) system.

Context from logs:
{context_text}

Question: {query}

Provide a detailed, actionable answer based on the log data. Include:
1. Summary of findings
2. Severity assessment
3. Specific recommendations
4. Technical details when relevant
                """.strip()

                response = llm.invoke(prompt)
                # langchain ChatGroq returns a BaseMessage; handle both message and string cases
                return getattr(response, "content", str(response))
        
        except Exception as e:
            return f"❌ Error: {str(e)}\n\nMake sure your Groq API key is valid."
    
    # Predefined prompts
    prompts = [
        ("🔐 Detect Security Threats", "security_threats"),
        ("⚠️ Analyze Errors (4xx/5xx)", "error_analysis"),
        ("⚡ Performance Issues", "performance_issues"),
        ("📈 Traffic Summary", "traffic_summary"),
        ("🔎 Anomaly Detection", "anomaly_detection"),
    ]
    
    # Create Gradio interface
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🛡️ Watermark Security Intelligence Chatbot")
        gr.Markdown("Analyze logs, detect threats, and get actionable security insights.")
        
        with gr.Row():
            api_key_input = gr.Textbox(
                label="Groq API Key",
                placeholder="Enter your Groq API key (get free at console.groq.com)",
                type="password",
                value=default_api_key or ""
            )
        
        gr.Markdown("### Quick Analysis")
        with gr.Row():
            results_box = gr.Textbox(label="Analysis Result", lines=15)
            for label, q in prompts:
                gr.Button(label).click(
                    fn=lambda api_key, query=q: handle_query(query, api_key),
                    inputs=[api_key_input],
                    outputs=results_box
                )
        
        gr.Markdown("### Ask a Question")
        with gr.Row():
            query_input = gr.Textbox(
                label="Your Question",
                placeholder="e.g., Why did the server crash? or Show me all brute force attempts",
                lines=2
            )
            submit_btn = gr.Button("Ask", variant="primary")
        
        output = gr.Textbox(label="Answer", lines=15)
        
        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, api_key_input],
            outputs=output
        )
        
        gr.Markdown("""
        ### Example Questions:
        - "What security threats were detected?"
        - "Why did user_5012 get a 500 error?"
        - "Show me all agent kill attempts"
        - "Which department has the most activity?"
        - "Explain the LDAP_Uri errors"
        """)
    
    return demo

# ============================================================================
# SECTION 7: MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow"""
    
    print("🚀 Initializing Watermark Security Chatbot...")
    
    # Step 1: Load data
    print("📊 Loading log data...")
    access_df, error_df = create_sample_data()
    print(f"✅ Loaded {len(access_df)} access logs and {len(error_df)} error logs")
    
    # Step 2: Initialize analyzer
    print("🔍 Initializing log analyzer...")
    analyzer = LogAnalyzer(access_df, error_df)
    
    # Step 3: Check for API key in environment variable
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    
    if groq_api_key:
        print("✅ Found Groq API key from environment variable")
    else:
        print("ℹ️  No API key found in environment variable (GROQ_API_KEY)")
        print("   You can enter it in the UI when prompted")
        print("   Get a free key at: https://console.groq.com/keys")
    
    # Step 4: Launch UI
    print("🎨 Launching interface on http://127.0.0.1:7860...")
    demo = create_ui(analyzer, default_api_key=groq_api_key)
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860, debug=True)

# Run the chatbot
if __name__ == "__main__":
    main()