import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AuthProvider } from "./auth/AuthContext";
import "./styles.css";

const root = createRoot(document.getElementById("root")!);

async function bootstrap() {
  try {
    const { App } = await import("./App");
    root.render(
      <StrictMode>
        <AuthProvider>
          <App />
        </AuthProvider>
      </StrictMode>,
    );
  } catch {
    root.render(
      <main id="main-content" className="startup-error">
        <section className="empty-state" role="alert" aria-labelledby="startup-error-heading">
          <p className="eyebrow">Configuration unavailable</p>
          <h1 id="startup-error-heading">The research interface could not start</h1>
          <p>
            This deployment is missing required public configuration. Ask the project
            administrator to verify the API and Firebase web settings, then reload the page.
          </p>
        </section>
      </main>,
    );
  }
}

void bootstrap();
