import React, { useState } from 'react';
import { useGroqChat } from '../hooks/useGroqChat';
import { ThreatCard } from './ThreatCard';
import { Controls } from './Controls';

const ChatPanel: React.FC = () => {
    const [userInput, setUserInput] = useState('');
    const { chatHistory, sendMessage } = useGroqChat();

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setUserInput(e.target.value);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (userInput.trim()) {
            sendMessage(userInput);
            setUserInput('');
        }
    };

    return (
        <div className="flex flex-col h-full p-4 bg-gradient-to-b from-black to-gray-800">
            <div className="flex-grow overflow-y-auto">
                {chatHistory.map((message, index) => (
                    <div key={index} className={`my-2 p-3 rounded-lg ${message.isUser ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-200'}`}>
                        {message.text}
                    </div>
                ))}
            </div>
            <form onSubmit={handleSubmit} className="flex mt-4">
                <input
                    type="text"
                    value={userInput}
                    onChange={handleInputChange}
                    placeholder="Type your message..."
                    className="flex-grow p-2 rounded-l-lg border border-gray-600 bg-gray-900 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <button type="submit" className="p-2 bg-purple-600 text-white rounded-r-lg hover:bg-purple-700 transition duration-200">
                    Send
                </button>
            </form>
            <Controls />
            <ThreatCard />
        </div>
    );
};

export default ChatPanel;