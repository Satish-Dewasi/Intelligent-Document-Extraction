import { useEffect, useState } from "react";
import { checkBackendHealth } from "./api/api";

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");

  useEffect(() => {
    checkBackendHealth()
      .then(() => {
        setBackendStatus("Connected");
      })
      .catch(() => {
        setBackendStatus("Disconnected");
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold">NeoStats Document Intelligence</h1>

      <p className="mt-2 text-gray-600">Document processing dashboard</p>

      <div className="mt-6 rounded-lg bg-white p-6 shadow">
        <p className="text-lg">
          Backend Status: <span className="font-semibold">{backendStatus}</span>
        </p>
      </div>
    </div>
  );
}

export default App;
