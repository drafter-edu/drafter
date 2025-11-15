export interface ClientBridgeWrapperInterface {
    goto(url: string, formData?: FormData): Promise<pyObject>;
}
