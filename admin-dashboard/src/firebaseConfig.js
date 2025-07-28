import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: "AIzaSyDD9hPA2SDMCVonEJPaJr_B4rmSUqfafmQ",
  authDomain: "enco-prestarail.firebaseapp.com",
  projectId: "enco-prestarail",
  storageBucket: "enco-prestarail.firebasestorage.app",
  messagingSenderId: "508735537545",
  appId: "1:508735537545:web:a3bcdddc4da18a15a6a158",
  measurementId: "G-CYXXBW62DN"
  // databaseURL: "https://enco-prestarail-default-rtdb.firebaseio.com", // optionnel, à activer si tu utilises la RTDB
};
export default firebaseConfig;

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app); 