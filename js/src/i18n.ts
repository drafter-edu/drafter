import i18next from "i18next";
import resources from "../locales/resources.json";

export const defaultNS = "common";

i18next.init({
    lng: "en",
    fallbackLng: "en",
    debug: false,

    ns: [defaultNS],
    defaultNS,

    resources,
});

export const t = i18next.t.bind(i18next);
export const i18n = i18next;
