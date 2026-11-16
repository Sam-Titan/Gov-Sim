import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import hi from "./hi.json";

const KEY = "govsim.lang";

function saved(): "en" | "hi" {
  try {
    const v = localStorage.getItem(KEY);
    return v === "hi" ? "hi" : "en";
  } catch {
    return "en";
  }
}

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, hi: { translation: hi } },
  lng: saved(),
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

i18n.on("languageChanged", (lng) => {
  try {
    localStorage.setItem(KEY, lng.startsWith("hi") ? "hi" : "en");
  } catch {
    // storage can be blocked; the choice then lasts for this visit only
  }
});

export default i18n;
