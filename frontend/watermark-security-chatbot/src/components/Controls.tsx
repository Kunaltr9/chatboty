import React from 'react';

const Controls: React.FC<{ onQuery: (query: string) => void }> = ({ onQuery }) => {
    const handleButtonClick = (query: string) => {
        onQuery(query);
    };

    return (
        <div className="flex flex-col items-center justify-center p-4 bg-gradient-to-r from-purple-600 to-blue-500 rounded-lg shadow-lg">
            <h2 className="text-white text-2xl font-bold mb-4">Quick Actions</h2>
            <div className="flex space-x-4">
                <button
                    className="bg-white text-purple-600 font-semibold py-2 px-4 rounded-full transition duration-300 ease-in-out transform hover:scale-105"
                    onClick={() => handleButtonClick("security_threats")}
                >
                    Detect Threats
                </button>
                <button
                    className="bg-white text-purple-600 font-semibold py-2 px-4 rounded-full transition duration-300 ease-in-out transform hover:scale-105"
                    onClick={() => handleButtonClick("error_analysis")}
                >
                    Analyze Errors
                </button>
                <button
                    className="bg-white text-purple-600 font-semibold py-2 px-4 rounded-full transition duration-300 ease-in-out transform hover:scale-105"
                    onClick={() => handleButtonClick("performance_issues")}
                >
                    Performance Issues
                </button>
                <button
                    className="bg-white text-purple-600 font-semibold py-2 px-4 rounded-full transition duration-300 ease-in-out transform hover:scale-105"
                    onClick={() => handleButtonClick("traffic_summary")}
                >
                    Traffic Summary
                </button>
                <button
                    className="bg-white text-purple-600 font-semibold py-2 px-4 rounded-full transition duration-300 ease-in-out transform hover:scale-105"
                    onClick={() => handleButtonClick("anomaly_detection")}
                >
                    Anomaly Detection
                </button>
            </div>
        </div>
    );
};

export default Controls;