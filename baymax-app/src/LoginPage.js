import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import './index.css';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';

function LoginPage() {
  const navigate = useNavigate();
  
  const handleGoogleLogin = async () => {
    try {
      const auth = getAuth();
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      
      // Authentication successful
      console.log("Authentication successful");
      
      // Navigate to dashboard after successful authentication
      navigate('/dashboard');
    } catch (error) {
      // Handle Errors here
      console.error("Authentication Error:", error);
      alert(`Login failed: ${error.message}`);
    }
  };
  
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-blue-100 px-4 text-center">
      {/* Floating BayMax Head */}
      <motion.div
        className="flex justify-center items-center mb-10"
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      >
        <div
          className="relative flex items-center justify-center rounded-full shadow-xl"
          style={{
            width: '500px',
            height: '260px',
            background: 'linear-gradient(to bottom, #ffffff, #f0f0f0)',
          }}
        >
          {/* Connector Line */}
          <div
            className="absolute top-1/2 transform -translate-y-1/2 h-1 bg-black z-0"
            style={{ width: '300px' }}
          />
          {/* Left Eye */}
          <motion.div
            className="w-16 h-16 bg-black rounded-full z-10"
            animate={{ scaleY: [1, 0.05, 1] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              repeatDelay: 4,
              ease: "easeInOut",
            }}
          />
          {/* Spacer */}
          <div style={{ width: '175px' }} />
          {/* Right Eye */}
          <motion.div
            className="w-16 h-16 bg-black rounded-full z-10"
            animate={{ scaleY: [1, 0.05, 1] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              repeatDelay: 4,
              ease: "easeInOut",
            }}
          />
        </div>
      </motion.div>
      {/* Greeting */}
      <motion.p
        className="text-xl font-medium text-black mb-6 max-w-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.2, ease: "easeOut", delay: 1 }}
      >
        Hi, I'm <strong>BayMax</strong>, your healthcare companion.
      </motion.p>
      {/* Login Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        className="px-8 py-3 rounded-full bg-white text-black shadow-md hover:shadow-lg hover:bg-gray-100 transition"
        onClick={handleGoogleLogin}
      >
        Log in with Google
      </motion.button>

    </div>
  );
}

export default LoginPage;