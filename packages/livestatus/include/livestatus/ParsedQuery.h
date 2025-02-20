// Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the
// terms and conditions defined in the file COPYING, which is part of this
// source code package.

#ifndef ParsedQuery_h
#define ParsedQuery_h

#include <chrono>
#include <functional>
#include <list>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_set>
#include <utility>
#include <vector>

#include "livestatus/Filter.h"
#include "livestatus/OutputBuffer.h"
#include "livestatus/Renderer.h"
#include "livestatus/RendererBrokenCSV.h"
#include "livestatus/Row.h"
#include "livestatus/StatsColumn.h"
#include "livestatus/Triggers.h"
#include "livestatus/User.h"
class Column;
class Table;

class ParsedQuery {
public:
    ParsedQuery(const std::list<std::string> &lines, const Table &table,
                OutputBuffer &output);

    std::unordered_set<std::string> all_column_names;
    std::vector<std::shared_ptr<Column>> columns;
    std::unique_ptr<Filter> filter;
    std::unique_ptr<Filter> wait_condition;
    std::vector<std::unique_ptr<StatsColumn>> stats_columns;
    bool show_column_headers{true};
    int limit{-1};
    std::optional<
        std::pair<std::chrono::seconds, std::chrono::steady_clock::time_point>>
        time_limit;
    CSVSeparators separators{"\n", ";", ",", "|"};
    OutputFormat output_format{OutputFormat::broken_csv};
    bool keepalive{false};
    OutputBuffer::ResponseHeader response_header{
        OutputBuffer::ResponseHeader::off};
    std::unique_ptr<const User> user;
    std::chrono::milliseconds wait_timeout{0};
    Triggers::Kind wait_trigger{Triggers::Kind::all};
    Row wait_object{nullptr};
    std::chrono::seconds timezone_offset{0};

private:
    using ColumnCreator =
        std::function<std::shared_ptr<Column>(std::string_view)>;

    using FilterStack = Filters;

    using LogicalConnective =
        std::function<std::unique_ptr<Filter>(Filter::Kind, const Filters &)>;

    void parseFilterLine(std::string_view line, FilterStack &filters,
                         const ColumnCreator &make_column);
    void parseStatsLine(std::string_view line,
                        const ColumnCreator &make_column);
    static void parseAndOrLine(std::string_view line, Filter::Kind kind,
                               const LogicalConnective &connective,
                               FilterStack &filters);
    static void parseNegateLine(std::string_view line, FilterStack &filters);
    void parseStatsAndOrLine(std::string_view line,
                             const LogicalConnective &connective);
    void parseStatsNegateLine(std::string_view line);
    void parseColumnsLine(std::string_view line,
                          const ColumnCreator &make_column);
    void parseColumnHeadersLine(std::string_view line);
    void parseLimitLine(std::string_view line);
    void parseTimelimitLine(std::string_view line);
    void parseSeparatorsLine(std::string_view line);
    void parseOutputFormatLine(std::string_view line);
    void parseKeepAliveLine(std::string_view line);
    void parseResponseHeaderLine(std::string_view line);
    void parseAuthUserHeader(
        std::string_view line,
        const std::function<std::unique_ptr<const User>(std::string_view name)>
            &find_user);
    void parseWaitTimeoutLine(std::string_view line);
    void parseWaitTriggerLine(std::string_view line);
    void parseWaitObjectLine(std::string_view line,
                             const std::function<Row(std::string_view)> &get);
    void parseLocaltimeLine(std::string_view line);
};

#endif  // ParsedQuery_h
