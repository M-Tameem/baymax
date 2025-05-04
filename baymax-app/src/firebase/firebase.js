// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCIJHhHxAYm3gTkrh5jzKMDPGRr7It2Ahs",
  authDomain: "baymaxai-55d37.firebaseapp.com",
  projectId: "baymaxai-55d37",
  storageBucket: "baymaxai-55d37.firebasestorage.app",
  messagingSenderId: "219798056072",
  appId: "1:219798056072:web:870fe14ce8cad740a8c33d",
  measurementId: "G-WG9ZYVXKMG"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { app, auth };