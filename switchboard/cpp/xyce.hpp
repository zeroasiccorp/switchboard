// Copyright (c) 2024 Zero ASIC Corporation
// This code is licensed under Apache License 2.0 (see LICENSE for details)

#include <map>
#include <string>
#include <vector>

#include <stdio.h>
#include <stdlib.h>

#include <N_CIR_XyceCInterface.h>

class XyceIntf {
  public:
    XyceIntf() {}

    ~XyceIntf() {
        if (m_opened) {
            xyce_close(m_xyceObj);
        }

        if (m_xyceObj) {
            free(m_xyceObj);
        }
    }

    void init(std::string file) {
        // pointer to N_CIR_Xyce object
        m_xyceObj = (void**)malloc(sizeof(void* [1]));

        // xyce command
        char* argList[] = {(char*)("Xyce"), (char*)("-quiet"), (char*)file.c_str()};
        int argc = sizeof(argList) / sizeof(argList[0]);
        char** argv = argList;

        // Open N_CIR_Xyce object
        xyce_open(m_xyceObj);
        m_opened = true;

        // Initialize N_CIR_Xyce object
        xyce_initialize(m_xyceObj, argc, argv);
        m_initialized = true;

        // Simulate for a small amount of time
        xyce_simulateUntil(m_xyceObj, 1e-10, &m_simTime);
    }

    void put(std::string name, double time, double value) {
        if (!m_time.count(name)) {
            m_time[name] = std::vector<double>();
        }

        m_time[name].push_back(time);

        if (!m_value.count(name)) {
            m_value[name] = std::vector<double>();
        }

        m_value[name].push_back(value);

        // TODO: prune old values for higher performance?

        if (m_initialized) {
            std::string fullName = "YDAC!" + name;

            xyce_updateTimeVoltagePairs(m_xyceObj, (char*)fullName.c_str(), m_time[name].size(),
                m_time[name].data(), m_value[name].data());
        }
    }

    void get(std::string name, double time, double* value) {
        if (m_initialized) {
            // advance simulation if necessary
            if (time > m_simTime) {
                int status = xyce_simulateUntil(m_xyceObj, time, &m_simTime);
            }

            // read out the value
            xyce_obtainResponse(m_xyceObj, (char*)name.c_str(), value);
        }
    }

  private:
    void** m_xyceObj;
    double m_simTime;
    bool m_opened;
    bool m_initialized;
    std::map<std::string, std::vector<double>> m_time;
    std::map<std::string, std::vector<double>> m_value;
};
