# Legacy code (archived)

This folder contains the original **FastAPI backend** and **React frontend** for AI Data Analyst, deployed on Render + Vercel.

## Why this was retired

The project migrated to a single-file **Streamlit app** (see `/streamlit_app` at the repo root). Reasons:

- **One service instead of two** - no more coordinating separate backend/frontend deploys.
- **No cold starts** - Render's free tier suspended after inactivity, requiring a keep-alive ping workaround. Streamlit Community Cloud doesn't have this problem for this use case.
- **Simpler for a single-user data tool** - the original split made sense for a multi-client API, but this app is a one-person analysis tool, so the extra infrastructure wasn't earning its keep.

## Status

This code is **not maintained** and **not part of the active deployment**. It's kept for reference only - e.g., if you want to see the original API design or extend this into a multi-user service later, where a real backend would make sense again.

The live app is at [askthedata-ai.streamlit.app](https://askthedata-ai.streamlit.app/), served from `/streamlit_app`.
