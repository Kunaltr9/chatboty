import { useState, useEffect } from 'react';

const useGroqChat = (apiKey) => {
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState(null);
    const [error, setError] = useState(null);

    const sendMessage = async (message) => {
        setLoading(true);
        setError(null);

        try {
            const res = await fetch('https://api.groq.com/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`,
                },
                body: JSON.stringify({ message }),
            });

            if (!res.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await res.json();
            setResponse(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return { loading, response, error, sendMessage };
};

export default useGroqChat;