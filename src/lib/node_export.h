#ifndef NODE_EXPORT_H_INCLUDED
#define NODE_EXPORT_H_INCLUDED

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Convert a single proxy link to target format (clash or singbox)
 *
 * @param link The proxy link (e.g., vmess://, ss://, vless://, trojan://, etc.)
 * @param target_format The target format: "clash" or "singbox"
 * @return JSON/YAML string containing the converted proxy node configuration.
 *         Returns NULL on error. Caller must free the returned string using free_result().
 */
char* convert_proxy_link(const char* link, const char* target_format);

/**
 * Convert multiple proxy links to target format (clash or singbox)
 *
 * @param links Multiple proxy links separated by newlines
 * @param target_format The target format: "clash" or "singbox"
 * @return JSON/YAML string containing the converted proxy nodes configuration.
 *         Returns NULL on error. Caller must free the returned string using free_result().
 */
char* convert_proxy_links(const char* links, const char* target_format);

/**
 * Convert subscription content to target format
 *
 * @param sub_content Base64 encoded subscription content or plain text with links
 * @param target_format The target format: "clash" or "singbox"
 * @param is_base64 1 if sub_content is base64 encoded, 0 otherwise
 * @return JSON/YAML string containing the converted proxy nodes configuration.
 *         Returns NULL on error. Caller must free the returned string using free_result().
 */
char* convert_subscription(const char* sub_content, const char* target_format, int is_base64);

/**
 * Free the memory allocated by convert_* functions
 *
 * @param result The string returned by convert_* functions
 */
void free_result(char* result);

/**
 * Get the last error message
 *
 * @return Error message string. Do not free this string.
 */
const char* get_last_error();

#ifdef __cplusplus
}
#endif

#endif // NODE_EXPORT_H_INCLUDED
