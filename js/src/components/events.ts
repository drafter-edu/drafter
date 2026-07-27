export const DRAFTER_PAGE_LOADED_EVENT = "drafter-page-loaded";

export type DrafterPageLoadedDetail = {
	requestId: number;
	responseId: number;
	route: string;
};
