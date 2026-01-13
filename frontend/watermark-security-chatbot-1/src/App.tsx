import React from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import Footer from './components/Footer';

const App: React.FC = () => {
    return (
        <div className="bg-black text-white min-h-screen flex flex-col">
            <Header />
            <div className="flex flex-1">
                <Sidebar />
                <ChatPanel />
            </div>
            <Footer />
        </div>
    );
};

export default App;