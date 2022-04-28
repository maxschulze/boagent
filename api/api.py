from fastapi import FastAPI
from subprocess import run
import time, json
from contextlib import redirect_stdout
from pprint import pprint
from openapi_client import ApiClient, Configuration
from openapi_client.api.component_api import ComponentApi
from openapi_client.model.cpu import Cpu
from openapi_client.model.ram import Ram
from openapi_client.model.disk import Disk
from openapi_client.model.mother_board import MotherBoard

hardware_file_name = "hardware_data.json"
impact_file_name = "impact_data.json"
app = FastAPI()

@app.get("/query")
async def query(start_time: float = 0.0, end_time: float = 0.0):
    now: float = time.time()
    if start_time == 0.0:
        start_time = now
    if end_time == 0.0:
        end_time += now + 30

    hardware_data = get_hardware_data()
    embedded_impact_data = get_embedded_impact_data(hardware_data)
    total_embedded_emissions = get_total_embedded_emissions(embedded_impact_data)

    res = {
        "start_time": start_time,
        "end_time": end_time,
        "hardware_data": hardware_data,
        "embedded_impact_data": embedded_impact_data,
        "power_data": "not implemented yet",
        "resources_data": "not implemented yet",
        "total_emissions": "not implemented yet",
        "total_power_consumption": "not implemented yet",
        "total_embedded_emissions": total_embedded_emissions,
        "total_operational_emissions": "not implemented yet"
    }

    return res

def get_total_embedded_emissions(embedded_impact_data):
    total = 0.0

    for d in embedded_impact_data['disks_impact']:
        total += float(d['impacts']['gwp']['manufacture'])

    for r in embedded_impact_data['rams_impact']:
        total += float(r['impacts']['gwp']['manufacture'])

    for c in embedded_impact_data['cpus_impact']:
        total += float(c['impacts']['gwp']['manufacture'])

    total += float(embedded_impact_data['motherboard_impact']['impacts']['gwp']['manufacture'])

    return round(total,1)

def get_hardware_data():
    hardware_cli = "../hardware/hardware.py"
    p = run([hardware_cli, "--output-file", hardware_file_name])
    with open(hardware_file_name, 'r') as fd:
        data = json.load(fd)
        return data

def get_embedded_impact_data(hardware_data):
    config = Configuration(
        host="http://localhost:5000",
    )
    client = ApiClient(
        configuration=config, pool_threads=2
    )
    component_api = ComponentApi(client)
    res_cpus = []
    for c in hardware_data['cpus']:
        cpu = Cpu(**c)
        res_cpus.append(component_api.cpu_impact_bottom_up_v1_component_cpu_post(cpu=cpu))
    res_rams = []
    for r in hardware_data['rams']:
        ram = Ram(**r)
        res_rams.append(component_api.ram_impact_bottom_up_v1_component_ram_post(ram=ram))

    res_disks = []
    for d in hardware_data['disks']:
        disk = Disk(**d)
        if d == "ssd":
            res_disks.append(component_api.disk_impact_bottom_up_v1_component_ssd_post(disk=disk))
        else:
            res_disks.append(component_api.disk_impact_bottom_up_v1_component_hdd_post(disk=disk))

    res_motherboard = component_api.motherboard_impact_bottom_up_v1_component_motherboard_post(mother_board=MotherBoard(**hardware_data['mother_board']))

    return {
        "disks_impact": res_disks,
        "rams_impact": res_rams,
        "cpus_impact": res_cpus,
        "motherboard_impact": res_motherboard
    }
    #impact_cli = "../impact/impact.py"
    #p = run([impact_cli, "--output-file", impact_file_name])
    ## define the entrypoint and parameters
    #with open(impact_file_name, 'r') as fd:
    #    data = json.load(fd)
    #    return data
