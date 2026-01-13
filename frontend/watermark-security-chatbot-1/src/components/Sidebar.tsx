import React from 'react';

const Sidebar: React.FC = () => {
    return (
        <div className="w-64 h-full bg-gradient-to-b from-black to-purple-900 p-4 shadow-lg">
            <h2 className="text-white text-2xl font-bold mb-6">Navigation</h2>
            <ul className="space-y-4">
                <li>
                    <a href="#" className="text-purple-300 hover:text-white transition duration-200">Home</a>
                </li>
                <li>
                    <a href="#" className="text-purple-300 hover:text-white transition duration-200">Threat Analysis</a>
                </li>
                <li>
                    <a href="#" className="text-purple-300 hover:text-white transition duration-200">Logs</a>
                </li>
                <li>
                    <a href="#" className="text-purple-300 hover:text-white transition duration-200">Settings</a>
                </li>
                <li>
                    <a href="#" className="text-purple-300 hover:text-white transition duration-200">Help</a>
                </li>
            </ul>
        </div>
    );
};

export default Sidebar;