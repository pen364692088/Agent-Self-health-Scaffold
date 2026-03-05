# spec

kind: let

source:
```prose
let spec = session: manager
  prompt: "Write SPEC.md + update README.md outline. Repo path: {project_path}"
```

---
Created a new specification document at `/home/moonlight/Project/Github/MyProject/PersonWebsite/CVWebsite/SPEC.md` covering scope, assumptions, acceptance criteria, architecture decisions (Astro + minimal JS), content modules (Home/About/Projects cards/Resume link/Contact), security constraints (no secrets, no destructive commands), and deployment strategy (GitHub Pages primary, Cloudflare Pages fallback).

Updated `/home/moonlight/Project/Github/MyProject/PersonWebsite/CVWebsite/README.md` with a concise project outline and a deployment section that includes GitHub Pages primary steps and Cloudflare Pages fallback placeholders.
