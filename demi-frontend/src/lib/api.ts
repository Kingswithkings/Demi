const API_BASE_URL =
  process.env.NEXT_PUBLIC_DEMI_API_URL || "http://127.0.0.1:8000";

export async function sendMessageToDemi(message: string) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
    }),
  });

  if (!response.ok) {
    throw new Error("Demi backend failed to respond");
  }

  return response.json();
}