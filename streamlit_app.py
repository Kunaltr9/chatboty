import streamlit as st

from appp import create_sample_data, LogAnalyzer


def main():
    st.set_page_config(page_title="Watermark Security Intelligence (Streamlit)", layout="wide")

    st.title("🛡️ Watermark Security Intelligence Dashboard")
    st.write("Analyze sample Apache logs, detect threats, and view summaries.")

    # Load data and analyzer (same sample data as Gradio app)
    access_df, error_df = create_sample_data()
    analyzer = LogAnalyzer(access_df, error_df)

    with st.sidebar:
        st.header("Groq Settings")
        groq_api_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Get a free key from console.groq.com",
        )

        analysis_choice = st.radio(
            "Quick analysis",
            [
                "Security threats",
                "Error analysis",
                "Performance issues",
                "Traffic summary",
                "Anomaly detection",
            ],
        )

    # Show raw data tabs
    tab1, tab2 = st.tabs(["Access Logs", "Error Logs"])
    with tab1:
        st.subheader("Access Logs")
        st.dataframe(access_df)
    with tab2:
        st.subheader("Error Logs")
        st.dataframe(error_df)

    st.markdown("---")

    # Quick analysis section
    st.subheader("Quick Analysis")

    if analysis_choice == "Security threats":
        threats = analyzer.detect_security_threats()
        if not threats:
            st.info("No major security threats detected in sample data.")
        else:
            for t in threats:
                st.markdown(f"**[{t['severity']}] {t['type']}**")
                st.write(f"- {t['details']}")
                st.write(f"- _Recommendation_: {t['recommendation']}")
                st.markdown("---")

    elif analysis_choice == "Error analysis":
        errors = analyzer.analyze_errors()
        if not errors:
            st.info("No significant 4xx/5xx errors detected.")
        else:
            for e in errors:
                st.markdown(f"**[{e['severity']}] {e['error_type']}**")
                st.write(f"- Count: {e.get('count', 'N/A')}")
                st.write(f"- _Fix_: {e['recommendation']}")
                st.markdown("---")

    elif analysis_choice == "Performance issues":
        issues = analyzer.detect_performance_issues()
        if not issues:
            st.info("No slow endpoints detected above threshold.")
        else:
            for i in issues:
                st.markdown(f"**[{i['severity']}] {i['endpoint']}**")
                st.write(f"- Avg: {i['avg_response_time']}, Peak: {i['peak_response_time']}")
                st.write(f"- _Optimization_: {i['optimization']}")
                st.markdown("---")

    elif analysis_choice == "Traffic summary":
        summary = analyzer.generate_traffic_summary()
        st.write(f"**Total Requests**: {summary['total_requests']}")
        st.write(f"**Error Rate**: {summary['error_rate']}")
        st.write("**Top Endpoints:**")
        for endpoint, count in summary["top_endpoints"].items():
            st.write(f"- {endpoint}: {count} requests")

    elif analysis_choice == "Anomaly detection":
        anomalies = analyzer.detect_anomalies()
        if not anomalies:
            st.info("No anomalies detected in sample data.")
        else:
            for a in anomalies:
                st.markdown(f"**[{a['severity']}] {a['type']}**")
                st.write(f"- {a['message']}")
                st.write(f"- Time: {a['timestamp']}")
                st.markdown("---")

    # Free-form question (delegates to Gradio/Groq path in future; here we just show hint)
    st.markdown("---")
    st.subheader("Ask a Question (LLM-backed)")
    st.write("For now, this Streamlit sample focuses on rule-based analysis and summaries.")
    st.write("Use the Gradio UI (via `appp.py`) with your Groq API key for full LLM-backed chat.")


if __name__ == "__main__":
    main()

