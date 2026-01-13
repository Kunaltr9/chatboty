import React from 'react';

const Footer: React.FC = () => {
    return (
        <footer className="bg-gradient-to-r from-purple-800 to-blue-600 text-white py-4">
            <div className="container mx-auto text-center">
                <p className="text-lg font-bold">Watermark Security Intelligence Chatbot</p>
                <p className="text-sm">© {new Date().getFullYear()} All Rights Reserved</p>
                <div className="mt-2">
                    <a href="/privacy" className="hover:underline">Privacy Policy</a>
                    <span className="mx-2">|</span>
                    <a href="/terms" className="hover:underline">Terms of Service</a>
                </div>
            </div>
        </footer>
    );
};

export default Footer;