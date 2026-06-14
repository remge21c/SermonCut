import React from "react";
import ReactDOM from "react-dom/client";
import { createHashRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import Home from "./screens/Home";
import QuickInput from "./screens/QuickInput";
import QuickCandidates from "./screens/QuickCandidates";
import QuickRenderSettings from "./screens/QuickRenderSettings";
import QuickResult from "./screens/QuickResult";
import "./styles.css";

// HashRouter: Electron file:// 환경에서 안전
const router = createHashRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: "quick/input", element: <QuickInput /> },
      { path: "quick/candidates", element: <QuickCandidates /> },
      { path: "quick/render", element: <QuickRenderSettings /> },
      { path: "quick/result", element: <QuickResult /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
