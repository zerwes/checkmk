// Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the
// terms and conditions defined in the file COPYING, which is part of this
// source code package.

#include "livestatus/TableServicesByHostGroup.h"

#include <functional>

#include "livestatus/Column.h"
#include "livestatus/ICore.h"
#include "livestatus/Interface.h"
#include "livestatus/Query.h"
#include "livestatus/Row.h"
#include "livestatus/TableHostGroups.h"
#include "livestatus/TableServices.h"
#include "livestatus/User.h"

namespace {
struct ServiceAndGroup {
    const IService *svc;
    const IHostGroup *group;
};
}  // namespace

TableServicesByHostGroup::TableServicesByHostGroup(ICore *mc) : Table(mc) {
    const ColumnOffsets offsets{};
    TableServices::addColumns(
        this, "",
        offsets.add([](Row r) { return r.rawData<ServiceAndGroup>()->svc; }),
        TableServices::AddHosts::yes, LockComments::yes, LockDowntimes::yes);
    TableHostGroups::addColumns(this, "hostgroup_", offsets.add([](Row r) {
        return r.rawData<ServiceAndGroup>()->group;
    }));
}

std::string TableServicesByHostGroup::name() const {
    return "servicesbyhostgroup";
}

std::string TableServicesByHostGroup::namePrefix() const { return "service_"; }

void TableServicesByHostGroup::answerQuery(Query &query, const User &user) {
    core()->all_of_host_groups([&user, &query](const IHostGroup &hg) {
        return hg.all([&hg, &user, &query](const IHost &host) {
            return host.all_of_services(
                [&hg, &user, &query](const IService &svc) {
                    ServiceAndGroup sag = {&svc, &hg};
                    return !user.is_authorized_for_service(svc) ||
                           query.processDataset(Row{&sag});
                });
        });
    });
}
