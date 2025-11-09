#include "node_export.h"

#include <cstring>
#include <string>
#include <vector>
#include <exception>

#include "parser/subparser.h"
#include "parser/config/proxy.h"
#include "generator/config/subexport.h"
#include "utils/base64/base64.h"
#include "utils/string.h"

// Thread-local error message storage
thread_local std::string g_last_error;

// Helper function to set error message
static void set_error(const std::string& error) {
    g_last_error = error;
}

// Helper function to convert std::string to char* (caller must free)
static char* string_to_cstr(const std::string& str) {
    if (str.empty()) {
        return nullptr;
    }
    char* result = new char[str.length() + 1];
    std::strcpy(result, str.c_str());
    return result;
}

// Helper function to configure extra_settings for node-only export
static void configure_node_export_settings(extra_settings& ext) {
    ext.nodelist = true;  // Only export nodes, no rules or groups
    ext.enable_rule_generator = false;
    ext.add_emoji = false;
    ext.remove_emoji = false;
    ext.append_proxy_type = false;
    ext.sort_flag = false;
    ext.filter_deprecated = false;
}

extern "C" {

char* convert_proxy_link(const char* link, const char* target_format) {
    if (!link || !target_format) {
        set_error("Invalid arguments: link or target_format is null");
        return nullptr;
    }

    try {
        std::string link_str(link);
        std::string format_str(target_format);

        // Parse the proxy link
        Proxy node;
        explode(link_str, node);

        // Check if parsing was successful
        if (node.Type == ProxyType::Unknown) {
            set_error("Failed to parse proxy link: unknown or invalid format");
            return nullptr;
        }

        // Create a vector with single node
        std::vector<Proxy> nodes;
        nodes.push_back(node);

        // Setup export settings
        extra_settings ext;
        configure_node_export_settings(ext);

        // Empty proxy groups and ruleset content (not needed for node-only export)
        ProxyGroupConfigs empty_groups;
        std::vector<RulesetContent> empty_rulesets;

        std::string output;

        // Convert to target format
        if (format_str == "clash" || format_str == "Clash") {
            std::string base_conf = "{}";  // Empty base config
            output = proxyToClash(nodes, base_conf, empty_rulesets, empty_groups, false, ext);
        } else if (format_str == "singbox" || format_str == "sing-box" || format_str == "SingBox") {
            std::string base_conf = "{}";  // Empty base config
            output = proxyToSingBox(nodes, base_conf, empty_rulesets, empty_groups, ext);
        } else {
            set_error("Invalid target_format: must be 'clash' or 'singbox'");
            return nullptr;
        }

        if (output.empty()) {
            set_error("Conversion failed: output is empty");
            return nullptr;
        }

        g_last_error.clear();
        return string_to_cstr(output);

    } catch (const std::exception& e) {
        set_error(std::string("Exception: ") + e.what());
        return nullptr;
    } catch (...) {
        set_error("Unknown exception occurred");
        return nullptr;
    }
}

char* convert_proxy_links(const char* links, const char* target_format) {
    if (!links || !target_format) {
        set_error("Invalid arguments: links or target_format is null");
        return nullptr;
    }

    try {
        std::string links_str(links);
        std::string format_str(target_format);

        // Split links by newline
        string_array link_list = split(links_str, "\n");

        if (link_list.empty()) {
            set_error("No valid links found in input");
            return nullptr;
        }

        // Parse all proxy links
        std::vector<Proxy> nodes;
        for (const auto& link : link_list) {
            std::string trimmed_link = trim(link);
            if (trimmed_link.empty() || trimmed_link[0] == '#') {
                continue;  // Skip empty lines and comments
            }

            Proxy node;
            try {
                explode(trimmed_link, node);
                if (node.Type != ProxyType::Unknown) {
                    nodes.push_back(node);
                }
            } catch (...) {
                // Skip invalid links but continue processing
                continue;
            }
        }

        if (nodes.empty()) {
            set_error("Failed to parse any valid proxy links");
            return nullptr;
        }

        // Setup export settings
        extra_settings ext;
        configure_node_export_settings(ext);

        // Empty proxy groups and ruleset content (not needed for node-only export)
        ProxyGroupConfigs empty_groups;
        std::vector<RulesetContent> empty_rulesets;

        std::string output;

        // Convert to target format
        if (format_str == "clash" || format_str == "Clash") {
            std::string base_conf = "{}";
            output = proxyToClash(nodes, base_conf, empty_rulesets, empty_groups, false, ext);
        } else if (format_str == "singbox" || format_str == "sing-box" || format_str == "SingBox") {
            std::string base_conf = "{}";
            output = proxyToSingBox(nodes, base_conf, empty_rulesets, empty_groups, ext);
        } else {
            set_error("Invalid target_format: must be 'clash' or 'singbox'");
            return nullptr;
        }

        if (output.empty()) {
            set_error("Conversion failed: output is empty");
            return nullptr;
        }

        g_last_error.clear();
        return string_to_cstr(output);

    } catch (const std::exception& e) {
        set_error(std::string("Exception: ") + e.what());
        return nullptr;
    } catch (...) {
        set_error("Unknown exception occurred");
        return nullptr;
    }
}

char* convert_subscription(const char* sub_content, const char* target_format, int is_base64) {
    if (!sub_content || !target_format) {
        set_error("Invalid arguments: sub_content or target_format is null");
        return nullptr;
    }

    try {
        std::string content(sub_content);
        std::string format_str(target_format);

        // Decode base64 if needed
        if (is_base64) {
            content = base64Decode(content);
        }

        // Parse subscription
        std::vector<Proxy> nodes;
        explodeSub(content, nodes);

        if (nodes.empty()) {
            set_error("Failed to parse subscription: no valid nodes found");
            return nullptr;
        }

        // Setup export settings
        extra_settings ext;
        configure_node_export_settings(ext);

        // Empty proxy groups and ruleset content
        ProxyGroupConfigs empty_groups;
        std::vector<RulesetContent> empty_rulesets;

        std::string output;

        // Convert to target format
        if (format_str == "clash" || format_str == "Clash") {
            std::string base_conf = "{}";
            output = proxyToClash(nodes, base_conf, empty_rulesets, empty_groups, false, ext);
        } else if (format_str == "singbox" || format_str == "sing-box" || format_str == "SingBox") {
            std::string base_conf = "{}";
            output = proxyToSingBox(nodes, base_conf, empty_rulesets, empty_groups, ext);
        } else {
            set_error("Invalid target_format: must be 'clash' or 'singbox'");
            return nullptr;
        }

        if (output.empty()) {
            set_error("Conversion failed: output is empty");
            return nullptr;
        }

        g_last_error.clear();
        return string_to_cstr(output);

    } catch (const std::exception& e) {
        set_error(std::string("Exception: ") + e.what());
        return nullptr;
    } catch (...) {
        set_error("Unknown exception occurred");
        return nullptr;
    }
}

void free_result(char* result) {
    if (result) {
        delete[] result;
    }
}

const char* get_last_error() {
    return g_last_error.c_str();
}

} // extern "C"
