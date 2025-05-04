import React, { useState, useEffect } from 'react';

function BaymaxPointer({ baymaxPosition }) {
  const [message, setMessage] = useState("Hello. I am Baymax, your personal healthcare companion.");
  
  useEffect(() => {
    // Messages that Baymax might say
    const messages = [
      "Hello. I am Baymax, your healthcare companion.",
      "Click 'Submit Order' to check drug interactions instantly.",
      "Need a quick overview? Tap 'Show Patient Summary' for clinical highlights.",
      "Not sure about discharge? Use the 'Check Discharge Eligibility' button.",
      "I can help flag dangerous drug combinations — just enter a new medication.",
      "You can switch patients using the dropdown at the top left.",
      "Don't forget to review allergies before placing a new drug order.",
      "You are doing an incredible job. Patient safety starts with you."
    ];
    
    let currentIndex = 0;
    const interval = setInterval(() => {
      setMessage(messages[currentIndex]);
      currentIndex = (currentIndex + 1) % messages.length; // loop back to start
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div
    className={`baymax-pointer transition-all duration-700 ease-in-out ${
      baymaxPosition === 'left' ? 'slide-in-left' : 'slide-in-right'
    }`}
    >
      <div className="baymax-head">
        <div className="baymax-body-shadow"></div>
        <div className="baymax-eyes">
          <div className="baymax-eye"></div>
          <div className="baymax-eye"></div>
        </div>
        <div className="baymax-speech-bubble">
          <p>{message}</p>
        </div>
      </div>
    </div>
  );
  
}

function DashboardPage() {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [newDrug, setNewDrug] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [ddiResults, setDdiResults] = useState(null);
  const [showSummary, setShowSummary] = useState(false);
  const [dischargeStatus, setDischargeStatus] = useState(null);
  const [checkingDischarge, setCheckingDischarge] = useState(false);
  const [baymaxPosition, setBaymaxPosition] = useState('right');
  const [selectedFile, setSelectedFile] = useState(null);
  const [aiSummary, setAiSummary] = useState(null);
  const [drugOrderResult, setDrugOrderResult] = useState(null);
  const [loadingAiSummary, setLoadingAiSummary] = useState(false);
  const [submittingDrug, setSubmittingDrug] = useState(false);


  const getAge = (birthDateStr) => {
    const birthDate = new Date(birthDateStr);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    return age - (today < new Date(today.getFullYear(), birthDate.getMonth(), birthDate.getDate()) ? 1 : 0);
  };
  
  const fetchPatients = async (newFileName = null) => {
    try {
      setLoading(true);
      const baseUrl = process.env.REACT_APP_API_BASE_URL || 'https://36d7-131-104-23-185.ngrok-free.app/';
      const response = await fetch(`${baseUrl}list-all-patients`, {
        headers: {
          "ngrok-skip-browser-warning": "true"
        }
      });
  
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const text = await response.text();
      let data;
  
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error("Invalid JSON response from server");
      }
  
      if (!data || !Array.isArray(data.patient_files)) {
        throw new Error("Unexpected response format from server");
      }
  
      const patientFiles = data.patient_files.filter(filename =>
        !filename.startsWith('hospital') &&
        !filename.startsWith('practitioner') &&
        filename.includes('_')
      );
  
      let patientList = patientFiles.map(filename => {
        const baseName = filename.replace(/\.json$/, ''); // remove extension
        const parts = baseName.split('_');
        if (parts.length >= 2) {
          const firstName = parts[0].replace(/[0-9]/g, '');
          const lastName = parts[1].replace(/[0-9]/g, '');
  
          const capitalize = str => str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
  
          return {
            id: filename,
            name: `${capitalize(lastName)}, ${capitalize(firstName)}`
          };
        }
        return null;
      }).filter(Boolean);
  
      if (newFileName) {
        patientList.sort((a, b) => (a.id === newFileName ? -1 : b.id === newFileName ? 1 : 0));
      }
  
      setPatients(patientList);
      if (patientList.length > 0) setSelectedPatient(patientList[0].id);
  
    } catch (err) {
      console.error("Failed to fetch patients:", err);
      setError("Failed to load patient list. Please try again later.");
    } finally {
      setLoading(false);
    }
  };
  

  useEffect(() => {
    fetchPatients();
  }, []);  

  useEffect(() => {
    if (!selectedPatient) return;

    const fetchSummary = async () => {
      try {
        const baseUrl = process.env.REACT_APP_API_BASE_URL || 'https://36d7-131-104-23-185.ngrok-free.app/';
        const response = await fetch(`${baseUrl}summary`, {
          method: 'POST',
          headers: {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
          },
          body: JSON.stringify({ file_path: `../data/fhir/${selectedPatient}` })
        });

        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const text = await response.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch {
          throw new Error("Invalid JSON in summary response");
        }
        setSummary(data);
      } catch (err) {
        console.error("Failed to fetch summary:", err);
        setSummary({ error: "Failed to load summary." });
      }
    };

    fetchSummary();
  }, [selectedPatient]);

const fetchAiSummary = async () => {
  if (!selectedPatient) return;

  setLoadingAiSummary(true);
  setAiSummary(null);

  try {
    const baseUrl = process.env.REACT_APP_API_BASE_URL || 'https://36d7-131-104-23-185.ngrok-free.app/';
    const response = await fetch(`${baseUrl}ai-summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
      body: JSON.stringify({ file_path: selectedPatient }),
    });

    if (!response.ok) throw new Error("Failed to fetch AI summary");

    const data = await response.json();
    setAiSummary(data?.summary || "No summary available.");
  } catch (err) {
    console.error("Failed to fetch AI summary:", err);
    setAiSummary("Failed to generate summary.");
  } finally {
    setLoadingAiSummary(false);
  }
};


  useEffect(() => {
    if (selectedPatient) {
      setDdiResults(null); // Clear previous DDI results when switching patients
    }
  }, [selectedPatient]);
  
  const handleSubmitDrug = async () => {
    if (!newDrug.trim() || !selectedPatient) return;
  
    setSubmittingDrug(true); // 🔒 Disable and show "Submitting..."
  
    setBaymaxPosition('right');
    const baseUrl = process.env.REACT_APP_API_BASE_URL || 'https://36d7-131-104-23-185.ngrok-free.app/';
    const payload = {
      file_path: selectedPatient,
      new_medication: newDrug.trim()
    };
  
    try {
      const response = await fetch(`${baseUrl}submit-drug-order`, {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true"
        },
        body: JSON.stringify(payload)
      });
  
      if (!response.ok) throw new Error(`Primary request failed: ${response.status}`);
      const data = await response.json();
  
      setDrugOrderResult(data);
      const ddiMatches = data?.safety_assessment?.drug_interactions || [];
      setDdiResults(ddiMatches);
      setNewDrug('');
    } catch (primaryErr) {
      console.warn("submit-drug-order failed, falling back to /match:", primaryErr);
  
      try {
        const fallback = await fetch(`${baseUrl}match`, {
          method: 'POST',
          headers: {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
          },
          body: JSON.stringify(payload)
        });
  
        if (!fallback.ok) throw new Error(`Fallback also failed: ${fallback.status}`);
        const fallbackData = await fallback.json();
  
        const fallbackDDI = fallbackData?.top_5_ddi_matches || [];
        setDdiResults(fallbackDDI);
        setNewDrug('');
      } catch (fallbackErr) {
        console.error("Both primary and fallback failed:", fallbackErr);
        setError("Failed to check drug interaction. Please try again later.");
      }
    } finally {
      setSubmittingDrug(false);
    }
  };  
  

  const handleCheckDischarge = async () => {
    if (!selectedPatient) return;
  
    setCheckingDischarge(true);
    setDischargeStatus(null);
  
    const baseUrl = process.env.REACT_APP_API_BASE_URL || 'https://36d7-131-104-23-185.ngrok-free.app/';
    const payload = { file_path: selectedPatient };
  
    console.log("Sending discharge request with payload:", payload);
  
    try {
      const response = await fetch(`${baseUrl}discharge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: JSON.stringify(payload),
      });
  
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  
      const data = await response.json();
      console.log("Received discharge response:", data);
  
      setDischargeStatus(data);
    } catch (err) {
      console.error("Discharge request failed:", err);
      setDischargeStatus({ decision: "Error", justification: "Failed to evaluate discharge." });
    } finally {
      setCheckingDischarge(false);
    }
  };
  

  return (
    <div className="baymax-dashboard">
      <style jsx global>{`
        /* Baymax Theme CSS */
        :root {
          --baymax-white: #f8f9fa;
          --baymax-black: #1a1a1a;
          --baymax-red: #ff6b6b;
          --baymax-primary: #3498db;
          --baymax-secondary: #e8f4fc;
          --baymax-accent: #f1c40f;
          --baymax-shadow: rgba(0, 0, 0, 0.1);
        }
        
        body {
          background-color: #f0f5f9;
          font-family: 'Nunito', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .baymax-dashboard {
          min-height: 100vh;
          background-color: white;
          padding: 2rem;
          color: #2c3e50;
        }
        
        .baymax-card {
          background-color: var(--baymax-white);
          border-radius: 24px;
          box-shadow: 0 6px 16px var(--baymax-shadow);
          padding: 1.5rem;
          transition: all 0.3s ease;
          border: none;
          overflow: hidden;
        }
        
        .baymax-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 12px 24px var(--baymax-shadow);
        }
        
        .baymax-title {
          color: #2980b9;
          font-weight: bold;
          margin-bottom: 1.5rem;
          border-bottom: 2px solid var(--baymax-secondary);
          padding-bottom: 0.75rem;
          position: relative;
        }
        
        .baymax-title:after {
          content: "";
          position: absolute;
          bottom: -2px;
          left: 0;
          width: 60px;
          height: 2px;
          background-color: var(--baymax-primary);
        }
        
        .baymax-button {
          background-color: var(--baymax-primary);
          color: white;
          border: none;
          border-radius: 50px;
          padding: 0.75rem 1.5rem;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 4px 6px rgba(52, 152, 219, 0.2);
        }
        
        .baymax-button:hover {
          background-color: #2980b9;
          transform: translateY(-2px);
          box-shadow: 0 6px 8px rgba(52, 152, 219, 0.3);
        }
        
        .baymax-button:disabled {
          background-color: #a0c9e7;
          cursor: not-allowed;
          transform: none;
          box-shadow: none;
        }
        
        .baymax-input {
          background-color: bg-gray-100; /* Light grey background */
          border: 2px solid #d3d3d3; /* Match border with background */
          border-radius: 50px;
          padding: 0.75rem 1.25rem;
          font-size: 1rem;
          transition: all 0.3s ease;
          width: 100%;
          color: #1a1a1a; /* Ensure text is readable */
        }        
        
        
        .baymax-input:focus {
          outline: none;
          border-color: #a9a9a9; /* Slightly darker grey */
          box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.1);
        }        
        
        .baymax-select {
          border: 2px solid #e2e8f0;
          border-radius: 50px;
          padding: 0.75rem 2.5rem 0.75rem 1.25rem;
          font-size: 1rem;
          transition: all 0.3s ease;
          width: 100%;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%232c3e50' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14L2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: calc(100% - 1rem) center;
        }
        
        .baymax-select:focus {
          outline: none;
          border-color: var(--baymax-primary);
          box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
        }
        
        .baymax-label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 600;
          color: #3a4a5a;
        }
        
        .baymax-grid {
          display: grid;
          gap: 2rem;
        }
        
        .baymax-section {
          margin-bottom: 1.5rem;
        }
        
        .baymax-section-title {
          color: #3a4a5a;
          font-weight: 600;
          margin-bottom: 0.75rem;
          padding-bottom: 0.5rem;
          border-bottom: 1px dashed #e2e8f0;
        }
        
        .baymax-list {
          list-style-type: none;
          padding-left: 0;
        }
        
        .baymax-list-item {
          padding: 0.5rem 0;
          border-bottom: 1px solid #f1f5f9;
        }
        
        .baymax-tag {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          border-radius: 50px;
          font-size: 0.875rem;
          font-weight: 600;
          margin-right: 0.5rem;
        }
        
        .baymax-tag-red {
          background-color: #ffe5e5;
          color: #e74c3c;
        }
        
        .baymax-tag-orange {
          background-color: #fff3e0;
          color: #e67e22;
        }
        
        .baymax-tag-blue {
          background-color: #e3f2fd;
          color: #3498db;
        }
        
        .baymax-tag-green {
          background-color: #e8f5e9;
          color: #2ecc71;
        }
        
        .baymax-loading {
          text-align: center;
          padding: 2rem;
          color: var(--baymax-primary);
        }
        
        .baymax-discharge {
          width: 160px;
          height: 160px;
          background: linear-gradient(45deg, #fff, #f8f9fa);
          border-radius: 50%;
          box-shadow: 
            0 8px 16px var(--baymax-shadow), 
            inset 0 -2px 10px rgba(0,0,0,0.05);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          color: #2c3e50;
          font-weight: bold;
          border: 3px solid #e8f4fc;
          font-size: 1.25rem;
          transition: all 0.3s ease;
          cursor: pointer;
          transform-origin: center;
        }
        
        .baymax-discharge:hover {
          transform: scale(1.05);
          box-shadow: 
            0 12px 24px var(--baymax-shadow), 
            inset 0 -2px 10px rgba(0,0,0,0.05);
        }
        
        .baymax-pointer {
          position: fixed;
          bottom: 2rem;
          right: 3rem; 
          z-index: 100;
          animation: float 3s ease-in-out infinite;
          transform-style: preserve-3d;
          perspective: 1000px;
        }        
        
        .baymax-head {
          position: relative;
          left: 15px;
          width: 200px;
          height: 170px;
          background-color: white;
          border-radius: 80% / 60%;
          box-shadow:
            0 8px 16px rgba(0, 0, 0, 0.1),
            inset 0 -8px 12px rgba(0, 0, 0, 0.05);
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.3s ease;
        }
        
        .baymax-head:hover {
          transform: rotate(0deg) scale(1.05);
        }
        
        .baymax-eyes {
          position: relative;
          width: 120px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        
        .baymax-eyes:after {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 80px;
          height: 4px;
          background-color: black;
          border-radius: 2px;
        }
        
        .baymax-eye {
          width: 23px;
          height: 23px;
          background-color: black;
          border-radius: 50%;
          z-index: 1;
        }
        
        .baymax-eye::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 0;
          right: 0;
          height: 2px;
          background-color: rgba(0, 0, 0, 0.2);
          transform: translateY(-50%);
          z-index: 0;
        }
        
        .baymax-speech-bubble {
          position: absolute;
          top: -90px;
          left: -20px;
          background-color: white;
          border-radius: 20px;
          padding: 15px;
          min-width: 220px;
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
          transform-origin: bottom left;
          animation: bobble 3s ease-in-out infinite;
          animation-delay: 0.5s;
        }
        
        @keyframes bobble {
          0%, 100% { transform: translateY(0) scale(1); }
          50% { transform: translateY(-5px) scale(1.02); }
        }
        
        .baymax-speech-bubble:after {
          content: '';
          position: absolute;
          bottom: -10px;
          left: 30px;
          width: 20px;
          height: 20px;
          background-color: white;
          transform: rotate(45deg);
          box-shadow: 5px 5px 8px rgba(0,0,0,0.05);
        }
        
        .baymax-speech-bubble p {
          margin: 0;
          font-size: 1.1rem;
          line-height: 1.5;
          color: #333;
        }
        
        .baymax-body-shadow {
          position: absolute;
          bottom: -15px;
          left: 50%;
          transform: translateX(-50%);
          width: 100px;
          height: 20px;
          background: radial-gradient(ellipse, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0) 70%);
          border-radius: 50%;
          z-index: -1;
          animation: shadow-pulse 3s ease-in-out infinite;
        }
        
        @keyframes shadow-pulse {
          0%, 100% { transform: translateX(-50%) scale(1); opacity: 0.2; }
          50% { transform: translateX(-50%) scale(0.8); opacity: 0.15; }
        }
        
        @keyframes float {
          0% {
            transform: translateY(0px) rotateY(0deg);
          }
          25% {
            transform: translateY(-8px) rotateY(5deg);
          }
          50% {
            transform: translateY(-10px) rotateY(0deg);
          }
          75% {
            transform: translateY(-5px) rotateY(-5deg);
          }
          100% {
            transform: translateY(0px) rotateY(0deg);
          }
        }

        @keyframes slideLeftOut {
          0% { right: 2rem; opacity: 1; }
          100% { right: -250px; opacity: 0; }
        }
        
        @keyframes slideRightOut {
          0% { left: 2rem; opacity: 1; }
          100% { left: -250px; opacity: 0; }
        }
        
        .slide-in-left {
          left: 2rem !important;
          right: auto !important;
          animation: slideRightOut 0.7s reverse forwards;
        }
        
        .slide-in-right {
          right: 2rem !important;
          left: auto !important;
          animation: slideLeftOut 0.7s reverse forwards;
        }
      `}</style>

      <h1 className="text-3xl font-bold mb-6 baymax-title">Patient Dashboard</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Patient + Drug Input */}
        <div className="baymax-card space-y-6" style={{ backgroundColor: '#e0f7fa' }}>
          {loading ? (
            <div className="baymax-loading">Loading patients...</div>
          ) : error ? (
            <div className="baymax-tag baymax-tag-red w-full text-center">{error}</div>
          ) : (
            <>
              <div>
                <label className="baymax-label">Select Patient</label>
                <select
                  className="baymax-select"
                  value={selectedPatient}
                  onChange={(e) => setSelectedPatient(e.target.value)}
                >
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>{patient.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
              <input
                id="file-upload"
                type="file"
                accept=".json"
                style={{ display: 'none' }}
                onChange={async (e) => {
                  const file = e.target.files[0];
                  if (!file || !file.name.endsWith('.json')) {
                    alert("Please upload a valid .json file.");
                    return;
                  }

                  setSelectedFile(file); // optional display

                  const formData = new FormData();
                  formData.append("file", file);

                  try {
                    const baseUrl = process.env.REACT_APP_API_BASE_URL || 'https://36d7-131-104-23-185.ngrok-free.app/';
                    const response = await fetch(`${baseUrl}upload-fhir`, {
                      method: "POST",
                      body: formData,
                      headers: {
                        "ngrok-skip-browser-warning": "true"
                      }
                    });

                    if (!response.ok) throw new Error("Upload failed.");

                    alert("File uploaded successfully.");
                    setSelectedFile(null);
                    await fetchPatients(file.name); // pass uploaded file name
                  } catch (err) {
                    console.error("Upload error:", err);
                    alert("Failed to upload file.");
                  }
                }}
              />

              <label htmlFor="file-upload" className="baymax-button cursor-pointer block text-center">
                Upload A Patient's Medical File – Choose a JSON File
              </label>

              {selectedFile && (
                <p className="text-sm text-gray-600 text-center">{selectedFile.name}</p>
              )}
            </div>



              <div>
                <label className="baymax-label">New Drug Order Check</label>
                <input
                  type="text"
                  className="baymax-input"
                  placeholder="e.g. Amoxicillin"
                  value={newDrug}
                  onChange={(e) => setNewDrug(e.target.value)}
                />
              </div>

              <button
                onClick={handleSubmitDrug}
                disabled={!newDrug.trim() || !selectedPatient || submittingDrug}
                className="baymax-button"
                style={submittingDrug ? { backgroundColor: '#ccc', cursor: 'not-allowed' } : {}}
              >
                {submittingDrug ? "Submitting..." : "Submit Order"}
              </button>
              
              {ddiResults !== null && (
                <div className="baymax-section mt-6">
                  {/* 1. Drug Interaction Check */}
                  <h4 className="baymax-section-title">Drug Interaction Check</h4>
                  {ddiResults.length === 0 ? (
                    <div className="baymax-tag baymax-tag-green">No known interactions. All clear!</div>
                  ) : (
                    <ul className="baymax-list">
                      {ddiResults.map((item, idx) => (
                        <li key={idx} className="baymax-list-item mb-2">
                          <div className={`baymax-tag ${
                            item.interaction.toLowerCase().includes('major') ? 'baymax-tag-red' :
                            item.interaction.toLowerCase().includes('moderate') ? 'baymax-tag-orange' :
                            'baymax-tag-blue'
                          }`}>
                            {item.interaction}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}

                  {/* 2. Contraindications */}
                  {Array.isArray(drugOrderResult?.safety_assessment?.contraindications) && (
                    <div className="baymax-section mt-6">
                      <h4 className="baymax-section-title">Contraindications</h4>
                      {drugOrderResult.safety_assessment.contraindications.length > 0 ? (
                        drugOrderResult.safety_assessment.contraindications.map((item, idx) => (
                          <div
                            key={idx}
                            className="bg-red-100 border border-red-300 text-red-800 p-4 rounded-lg mb-4 whitespace-pre-line"
                          >
                            {item.text}
                            <div className="text-sm text-red-600 mt-2">
                              Similarity Score: {item.similarity.toFixed(2)}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="baymax-tag baymax-tag-green">
                          No contraindications found.
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* 3. AI Assessment */}
                    {drugOrderResult?.safety_assessment?.ai_assessment && (
                      <div className="baymax-section mt-6">
                        <h4 className="baymax-section-title">AI Assessment</h4>
                        {(() => {
                          const assessment = drugOrderResult.safety_assessment.ai_assessment;
                          const [justificationRaw, recommendationRaw] = assessment.split("**Recommendation:**");

                          const formatJustification = (text) =>
                            text.trim().replace(/\n/g, "<br/>");

                          const formatRecommendation = (text) =>
                            text
                              .trim()
                              .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#e74c3c;">$1</strong>')
                              .replace(/\n/g, "<br/>");

                          return (
                            <>
                              {justificationRaw && (
                                <div className="p-4 bg-green-50 border-l-4 border-green-400 text-green-900 rounded whitespace-pre-line mb-4">
                                  <strong className="block mb-1">Key Concerns:</strong>
                                  <div
                                    dangerouslySetInnerHTML={{
                                      __html: formatJustification(justificationRaw),
                                    }}
                                  />
                                </div>
                              )}

                              {recommendationRaw && (
                                <div className="p-4 bg-green-50 border-l-4 border-green-400 text-green-900 rounded whitespace-pre-line">
                                  <strong className="block mb-1">Recommendation:</strong>
                                  <div
                                    dangerouslySetInnerHTML={{
                                      __html: formatRecommendation(recommendationRaw),
                                    }}
                                  />
                                </div>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Right: Patient Summary */}
        <div className="space-y-6">

        {/* Discharge Status */}
        <div className="bg-white rounded-2xl shadow-md p-6 mb-6" style={{ backgroundColor: '#e0f7fa' }}>
          <h2 className="text-xl font-semibold mb-4">Discharge Evaluation</h2>

          <button
            onClick={handleCheckDischarge}
            className="baymax-button mb-4"
            disabled={checkingDischarge}
          >
            {checkingDischarge ? "Checking..." : "Check Discharge Eligibility"}
          </button>

          {dischargeStatus && (
            <div className="mt-2 p-3 bg-white rounded shadow text-sm border border-gray-200">
              <p>
                <strong>Decision:</strong>{" "}
                <span className={
                  dischargeStatus.decision.toLowerCase() === 'yes' ? 'text-green-600 font-semibold' :
                  dischargeStatus.decision.toLowerCase() === 'absolutely not' ? 'text-red-600 font-semibold' :
                  'text-blue-600 font-semibold'
                }>
                  {dischargeStatus.decision}
                </span>
              </p>
              <p className="mt-1 text-gray-700"><strong>Justification:</strong> {dischargeStatus.justification}</p>
            </div>
          )}
        </div>

        {/* Patient Summary */}
        <div className="bg-gray-100 rounded-2xl shadow-md p-6 space-y-4">
        {/* Updated AI Summary rendering to handle object format */}
          
        <div className="mb-4">
          <button 
            className="baymax-button"
            onClick={fetchAiSummary}
            disabled={loadingAiSummary}
          >
            {loadingAiSummary ? "Generating..." : "Generate AI Summary"}
          </button>
        </div>


          {aiSummary && (
            typeof aiSummary === 'string' ? (
              <p className="text-gray-800 whitespace-pre-line">{aiSummary}</p>
            ) : (
              Object.entries(aiSummary).map(([key, value]) => (
                <div key={key} className="mb-3">
                  <p className="font-semibold">{key}</p>
                  <p className="text-gray-700 whitespace-pre-line">
                    {typeof value === 'string' 
                      ? value 
                      : typeof value === 'object' 
                        ? JSON.stringify(value, null, 2) 
                        : String(value)}
                  </p>
                </div>
              ))
            )
          )}


        <button 
          className="baymax-button"
          onClick={() => {
            setShowSummary(prev => {
              const newState = !prev;
              setBaymaxPosition(newState ? 'left' : 'right');
              return newState;
            });
          }}
        >
          {showSummary ? "Hide" : "Show"} Patient Summary
        </button>
        
          {!selectedPatient && <p>No patient selected.</p>}

          {showSummary && selectedPatient && (
            <div className="space-y-2">
              <p><span className="font-medium">Selected:</span> {patients.find(p => p.id === selectedPatient)?.name || ''}</p>

              {summary?.error ? (
                <p className="bg-red-100 text-red-700 p-2 rounded">{summary.error}</p>
              ) : summary ? (
                <div className="space-y-4 text-base leading-relaxed">
                  {/* Demographics */}
                  {summary.demographics && (
                    <div>
                      <h3 className="text-md font-semibold border-b pb-1">Demographics</h3>
                      <p><strong>Name:</strong> {summary.demographics.name}</p>
                      <p><strong>Gender:</strong> {summary.demographics.gender}</p>
                      <p><strong>Age:</strong> {getAge(summary.demographics.birthDate)} ({summary.demographics.birthDate})</p>
                    </div>
                  )}

                  {/* Medications */}
                  {summary.medications_all_time?.length > 0 && (
                    <div>
                      <h3 className="text-md font-semibold border-b pb-1">Medications</h3>
                      <ul className="list-disc list-inside">
                        {summary.medications_all_time.map((med, idx) => (
                          <li key={idx}>{med.medication} ({med.status})</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Conditions */}
                  {summary.conditions_all_time?.length > 0 && (
                    <div>
                      <h3 className="text-md font-semibold border-b pb-1">Conditions</h3>
                      <ul className="list-disc list-inside">
                        {summary.conditions_all_time.map((cond, idx) => (
                          <li key={idx}>
                            <strong>{cond.code}</strong> <br />
                            <span className="text-gray-600 text-xs">Onset: {new Date(cond.onset).toLocaleDateString()}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Vitals */}
                  {summary.recent_vitals && (
                    <div>
                      <h3 className="text-md font-semibold border-b pb-1">Recent Vitals</h3>
                      <ul className="list-disc list-inside">
                        {Object.entries(summary.recent_vitals).map(([key, val]) => (
                          <li key={key}>
                            {key}: {val.value ?? 'N/A'} <br />
                            <span className="text-gray-600 text-xs">Date: {new Date(val.date).toLocaleDateString()}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Labs */}
                  {summary.recent_labs && (
                    <div>
                      <h3 className="text-md font-semibold border-b pb-1">Recent Lab Results</h3>
                      <ul className="list-disc list-inside">
                        {Object.entries(summary.recent_labs).map(([key, val]) => (
                          <li key={key}>
                            {key}: {val.value ?? 'N/A'} <br />
                            <span className="text-gray-600 text-xs">Date: {new Date(val.date).toLocaleDateString()}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Allergies */}
                  <div>
                    <h3 className="text-md font-semibold border-b pb-1">Allergies</h3>
                    <p>{summary.allergies?.length ? summary.allergies.join(', ') : 'None reported'}</p>
                  </div>
                </div>
              ) : (
                <p className="text-blue-500">Loading summary...</p>
              )}
            </div>
          )}
        </div>
        </div>

      </div> {/* Close baymax-grid */}

      {/* Baymax character */}
    
      <BaymaxPointer baymaxPosition={baymaxPosition} />
    </div>
  );
}

export default DashboardPage;