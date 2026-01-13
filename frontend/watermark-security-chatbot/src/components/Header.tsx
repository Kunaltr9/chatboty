import React from 'react';

const Header: React.FC = () => {
    return (
        <header className="bg-gradient-to-r from-purple-800 to-blue-600 text-white shadow-lg sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
                <h1 className="text-2xl font-bold">Watermark Security Chatbot</h1>
                <nav className="space-x-4">
                    <a href="#home" className="hover:text-gray-200 transition duration-300">Home</a>
                    <a href="#about" className="hover:text-gray-200 transition duration-300">About</a>
                    <a href="#contact" className="hover:text-gray-200 transition duration-300">Contact</a>
                </nav>
            </div>
        </header>
    );
};

export default Header;