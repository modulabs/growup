import { p as public_env } from "./shared-server.js";
import "@sveltejs/kit/internal/server";
import "clsx";
import "./auth.js";
public_env.PUBLIC_API_BASE_URL || "https://modulabs.ddns.net/growup";
