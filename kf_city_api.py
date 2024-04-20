from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
import json
# from frappe.utils.user import get_user_fullname
from frappe.core.doctype.user.user import generate_keys
import requests
from frappe.utils import cint, cstr, flt, formatdate, getdate, now, today


# #login API
@frappe.whitelist(allow_guest=True)
def login_api(data=None):
	data = json.loads(frappe.request.data)
	# url = "https://dev-kfm.indictranstech.com/api/method/login"
	url = "http://localhost:8000/api/method/login"
	response=requests.post(url, data={"usr":data.get("username"), "pwd":data.get("password")})
	if response.status_code == 200:
		response_text = json.loads(response.text)
		token=generate_token(data)
		response_text["Authorization"] = token.get("Authorization")
		response_text["email_id"] = frappe.db.get_value("User", data.get("username"), "email")
		response_text["roles"] = frappe.get_roles(data.get("username"))
		response_text["user_id"] = frappe.db.get_value("User Details",{"user_email":data.get("username")},"name")
		return {"status_code":200, "success":True, "error":"", "data":response_text}
	else:
		return {"status_code":401, "success":False, "error":"Invalid Username or Password"}

def generate_token(data=None):
	user_details = frappe.get_doc("User", data.get("username"))
	api_secret = frappe.generate_hash(length=15)
	# if api key is not set generate api key
	if not user_details.api_key:
		api_key = frappe.generate_hash(length=15)
		user_details.api_key = api_key
	user_details.api_secret = api_secret
	user_details.save(ignore_permissions=True)

	generated_secret = frappe.utils.password.get_decrypted_password("User", data.get("username"), fieldname='api_secret')
	api_key = frappe.db.get_value("User", data.get("username"), "api_key")
	return {"status":200, "Authorization": "token {}:{}".format(api_key, generated_secret), "response":"Successfully"}


# #Get purticular asset details
# @frappe.whitelist()
# def asset_details_api(data=None):
# 	data = json.loads(frappe.request.data)
# 	try:
# 		asset_details = frappe.db.sql("""SELECT name as asset_id, asset_code, asset_name, asset_owner, status, specifications, serial_number, sap_id, date_of_commissioning, date_of_installation, planned_hours_per_month, asset_category, asset_sub_category, asset_type, equipment_brand, equipment_model, equipment_life, is_purchased, vendor_name, po_number, po_amount, purchase_date, under_warranty, warranty_expiry, email_id, customer, facility from `tabAsset Register` where name='{0}' """.format(data.get("asset_id")), as_dict=1)
# 		return {"status_code":200, "success":True, "error":"", "data":asset_details}
# 	except Exception as e:
# 		return {"status_code":401, "success":False, "error":e}

#Get purticular asset details
@frappe.whitelist()
def asset_details_api(data=None):
	data = json.loads(frappe.request.data)
	customer, region, city, facility=user_access_details(data.get("username"))

	try:
		asset_details = frappe.db.sql("""SELECT name as asset_id, asset_code, asset_name, asset_owner, status, specifications, serial_number, sap_id, date_of_commissioning, date_of_installation, planned_hours_per_month, asset_category, asset_sub_category, asset_type, equipment_brand, equipment_model, equipment_life, is_purchased, vendor_name, po_number, po_amount, purchase_date, under_warranty, warranty_expiry, email_id, customer, facility from `tabAsset Register` where customer in ({1}) and facility in ({2}) and city in ({3}) and region in ({4}) and name='{0}' """.format(data.get("asset_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":asset_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

# #Get all kf assets details
@frappe.whitelist(allow_guest=True)
def get_all_assets():
	data = json.loads(frappe.request.data)
	offset = (cint(data.get("limit"))*cint(data.get("offSet"))) - cint(data.get("limit"))	
	if offset < 0 or data.get("name"):
		offset = 0

	customer, region, city, facility=user_access_details(data.get("username"))

	try:
		asset_details = frappe.db.sql("""SELECT name as asset_id, asset_code, asset_name, asset_owner, status, specifications, serial_number, sap_id, date_of_commissioning, date_of_installation, planned_hours_per_month, asset_category, asset_sub_category, asset_type, equipment_brand, equipment_model, equipment_life, is_purchased, vendor_name, po_number, po_amount, purchase_date, under_warranty, warranty_expiry, email_id, customer, facility, city, region from `tabAsset Register` where customer in ({3}) and facility in ({4}) and city in ({5}) and region in ({6}) and {0} order by modified desc limit {1} offSet {2} """.format(get_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":asset_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

def get_filters_codition(data):
        conditions = "1=1"
        if data.get("asset_id"):
            conditions += " and name = '{0}'".format(data.get('asset_id'))
        if data.get("status"):
            conditions += " and status = '{0}'".format(data.get('status'))
        if data.get("asset_category"):
            conditions += " and asset_category = '{0}'".format(data.get('asset_category'))
        if data.get("asset_sub_category"):
            conditions += " and asset_sub_category = '{0}'".format(data.get('asset_sub_category'))
        if data.get("asset_type"):
            conditions += " and asset_type = '{0}'".format(data.get('asset_type'))
        return conditions


@frappe.whitelist()
def get_user_profile_details(data=None):
	data = json.loads(frappe.request.data)
	try:
		user_profile = frappe.db.get_values("User", {"name":data.get("username")}, ["name", "email", "last_name", "language", "first_name", "full_name", "middle_name", "username", "gender", "birth_date", "phone", "location", "bio", "mobile_no"], as_dict=1)
		user_profile[0]["roles"] = frappe.get_roles(data.get("username"))
		return {"status_code":200, "success":True, "error":"", "data":user_profile[0]}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def create_new_asset():
	data = json.loads(frappe.request.data)
	try:
		addr_name = frappe.db.get_value("Dynamic Link", {"link_name":data.get("customer")}, "parent")
		address = frappe.db.get_values("Address", {"name":addr_name}, ["kf_region", "kf_city"]) 

		asset = frappe.new_doc("Asset Register")
		asset.asset_code = data.get("asset_code")
		asset.asset_name = data.get("asset_name") 
		asset.status = data.get("status")
		asset.asset_owner = data.get("asset_owner") 
		asset.specifications = data.get("specifications") 
		asset.serial_number = data.get("serial_number") 
		asset.sap_id = data.get("sap_id") 
		asset.date_of_commissioning = data.get("date_of_commissioning") 
		asset.date_of_installation = data.get("date_of_installation")
		asset.planned_hours_per_month = data.get("planned_hours_per_month")
		asset.asset_category = data.get("asset_category")
		asset.asset_sub_category = data.get("asset_sub_category")
		asset.asset_type = data.get("asset_type")
		asset.equipment_brand = data.get("equipment_brand")
		asset.equipment_model = data.get("equipment_model")
		asset.equipment_life = data.get("equipment_life")
		asset.is_purchased = data.get("is_purchased")
		asset.vendor_name = data.get("vendor_name")
		asset.po_number = data.get("po_number")
		asset.po_amount = data.get("po_amount")
		asset.purchase_date = data.get("purchase_date")
		asset.under_warranty = data.get("under_warranty")
		asset.warranty_expiry = data.get("warranty_expiry")
		asset.email_id = data.get("email_id")
		asset.customer = data.get("customer")
		asset.facility = addr_name if addr_name else ""
		asset.region = address[0][0] if address[0][0] else ""
		asset.city = address[0][1] if address[0][1] else ""
		asset.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status_code":200, "success":True, "error":"", "data":asset}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def update_asset_register():
	data = json.loads(frappe.request.data)
	addr_name = frappe.db.get_value("Dynamic Link", {"link_name":data.get("customer")}, "parent")
	address = frappe.db.get_values("Address", {"name":addr_name}, ["kf_region", "kf_city"])

	try:
		asset = frappe.get_doc("Asset Register", data.get("asset_id"))
		asset.asset_code = data.get("asset_code")
		asset.asset_name = data.get("asset_name") 
		asset.status = data.get("status") 
		asset.specifications = data.get("specifications") 
		asset.serial_number = data.get("serial_number") 
		asset.sap_id = data.get("sap_id") 
		asset.date_of_commissioning = data.get("date_of_commissioning") 
		asset.date_of_installation = data.get("date_of_installation")
		asset.planned_hours_per_month = data.get("planned_hours_per_month")
		asset.asset_category = data.get("asset_category")
		asset.asset_sub_category = data.get("asset_sub_category")
		asset.asset_type = data.get("asset_type")
		asset.equipment_brand = data.get("equipment_brand")
		asset.equipment_model = data.get("equipment_model")
		asset.equipment_life = data.get("equipment_life")
		asset.is_purchased = data.get("is_purchased")
		asset.vendor_name = data.get("vendor_name")
		asset.po_number = data.get("po_number")
		asset.po_amount = data.get("po_amount")
		asset.purchase_date = data.get("purchase_date")
		asset.under_warranty = data.get("under_warranty")
		asset.warranty_expiry = data.get("warranty_expiry")
		asset.email_id = data.get("email_id")
		asset.customer = data.get("customer")
		asset.facility = addr_name if addr_name else ""
		asset.region = address[0][0] if address[0][0] else ""
		asset.city = address[0][1] if address[0][1] else ""
		asset.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status_code":200, "success":True, "error":"", "data":asset}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def fetch_asset():
	data = json.loads(frappe.request.data)
	customer, region, city, facility=user_access_details(data.get("username"))
	try:
		data_dict = {}
		breakdown = frappe.db.sql("""SELECT name from `tabBreakdown` where status in ('Pending', 'WIP', 'Waiting for resources') and customer in ({1}) and facility in ({2}) and city in ({3}) and region in ({4}) and asset_id = '{0}' ORDER BY creation DESC """.format(data.get("asset_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		
		amc_schedule = frappe.db.sql("""SELECT name from `tabAMC Scheduling` where status = 'Under AMC' and asset_id = '{0}' and customer in ({1}) and facility in ({2}) and city in ({3}) and region in ({4}) ORDER BY creation DESC""".format(data.get("asset_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		
		ppm_schedule = frappe.db.sql("""SELECT name from `tabPPM Scheduling` where status = 'Under AMC' and asset_id = '{0}' and customer in ({1}) and facility in ({2}) and city in ({3}) and region in ({4}) ORDER BY creation DESC""".format(data.get("asset_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		
		data_dict["asset_id"] = data.get("asset_id")
		data_dict["breakdown_id"] = breakdown[0].get("name") if breakdown else ""
		data_dict["amc_scheduling_id"] = amc_schedule[0].get("name") if amc_schedule else ""
		data_dict["ppm_scheduling_id"] = ppm_schedule[0].get("name") if ppm_schedule else "" 
		return {"status_code":200, "success":True, "error":"", "data":data_dict}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def asset_list():
	data = json.loads(frappe.request.data)
	offset = (cint(data.get("limit"))*cint(data.get("offSet"))) - cint(data.get("limit"))	
	if offset < 0 or data.get("name"):
		offset = 0
	customer, region, city, facility=user_access_details(data.get("username"))
	try:
		if "System Manager" in roles:
			asset_details = frappe.db.sql("""SELECT name as asset_id, asset_name, asset_code, status, asset_category from `tabAsset Register` where (name like '{3}' or asset_name like '{3}') and {0} order by modified desc limit {1} offSet {2} """.format(asset_list_filters_codition(data),cint(data.get("limit")), offset, search), as_dict=1)
		else:
			asset_details = frappe.db.sql("""SELECT name as asset_id, asset_name, asset_code, status, asset_category from `tabAsset Register` where customer in ({3}) and facility in ({4}) and (name like '{5}' or asset_name like '{5}') and {0} order by modified desc limit {1} offSet {2} """.format(asset_list_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), search), as_dict=1)
			if not asset_details:
				asset_details = frappe.db.sql("""SELECT name as asset_id, asset_name, asset_code, status, asset_category from `tabAsset Register` where customer in ({3}) and facility in ({4}) and name like '{5}' or asset_name like '{5}' and {0} order by modified desc limit {1} """.format(asset_list_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), search), as_dict=1, debug=0)
		total_records = len(frappe.get_all('Asset Register'))
		return {"status_code":200, "success":True, "error":"", "total_records":total_records, "data":asset_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


def asset_list_filters_codition(data):
        conditions = "1=1"
        if data.get("status"):
            conditions += " and status = '{0}'".format(data.get('status'))
        if data.get("asset_category"):
            conditions += " and asset_category = '{0}'".format(data.get('asset_category'))
        return conditions



@frappe.whitelist()
def ppm_scheduling_details():
	data = json.loads(frappe.request.data)

	customer, region, city, facility=user_access_details(data.get("username"))

	try:
		ppm_schedule = frappe.db.sql("""SELECT name as ppm_scheduling_id, asset_id, asset_name, asset_code, serial_number, status, start_date, end_date, customer, facility, region, city From `tabPPM Scheduling` where name='{0}' and customer in ({1}) and facility in ({2}) and city in ({3}) and region in ({4})""".format(data.get("ppm_scheduling_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":ppm_schedule}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def update_ppm_scheduling():
	data=json.loads(frappe.request.data)
	try:
		if frappe.db.get_value("PPM Scheduling", {"name":data.get("ppm_scheduling_id")}, "name"):
			ppm_schedule = frappe.get_doc("PPM Scheduling", data.get("ppm_scheduling_id"))
			ppm_schedule.asset_id = data.get("asset_id")
			ppm_schedule.asset_name = data.get("asset_name")
			ppm_schedule.asset_code = data.get("asset_code")
			ppm_schedule.serial_number = data.get("serial_number")
			ppm_schedule.status = data.get("status")
			ppm_schedule.start_date = data.get("start_date")
			ppm_schedule.end_date = data.get("end_date")
			ppm_schedule.customer = data.get("customer")
			ppm_schedule.facility = data.get("facility")
			ppm_schedule.region = data.get("region")
			ppm_schedule.city = data.get("city")
			ppm_schedule.save(ignore_permissions=True)
			frappe.db.commit()
			return {"status_code":200, "success":True, "error":"", "data":ppm_schedule}
		else:
			return {"status_code":200, "success":True, "error":"", "data":[]}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

#Get all ppm_scheduling
@frappe.whitelist()
def get_ppm_scheduling_details():
	data = json.loads(frappe.request.data)
	offset = (cint(data.get("limit"))*cint(data.get("offSet"))) - cint(data.get("limit"))	
	if offset < 0 or data.get("name"):
		offset = 0

	customer, region, city, facility=user_access_details(data.get("username"))

	try:
		ppm_details = frappe.db.sql("""SELECT name as ppm_scheduling_id, asset_id, asset_name, asset_code, serial_number, status, start_date, end_date, customer, facility, region, city From `tabPPM Scheduling` where customer in ({3}) and facility in ({4}) and city in ({5}) and region in ({6}) and {0} order by modified desc limit {1} offSet {2} """.format(get_ppm_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":ppm_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

def get_ppm_filters_codition(data):
        conditions = "1=1"
        if data.get("ppm_scheduling_id"):
            conditions += " and name = '{0}'".format(data.get('ppm_scheduling_id'))
        if data.get("status"):
            conditions += " and status = '{0}'".format(data.get('status'))
        return conditions

@frappe.whitelist()
def get_ppm_scheduling_list():
	data = json.loads(frappe.request.data)
	offset = (cint(data.get("limit"))*cint(data.get("offSet"))) - cint(data.get("limit"))	
	if offset < 0 or data.get("name"):
		offset = 0

	customer, region, city, facility=user_access_details(data.get("username"))

	try:
		ppm_details = frappe.db.sql("""SELECT name as ppm_scheduling_id, status From `tabPPM Scheduling` where customer in ({3}) and facility in ({4}) and city in ({5}) and region in ({6}) and {0} order by modified desc limit {1} offSet {2} """.format(ppm_list_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		if not ppm_details:
			ppm_details = frappe.db.sql("""SELECT name as ppm_scheduling_id, status From `tabPPM Scheduling` where customer in ({3}) and facility in ({4}) and city in ({5}) and region in ({6}) and {0} order by modified desc limit {1} offSet {2} """.format(ppm_list_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		total_records = len(frappe.get_all('PPM Scheduling'))
		return {"status":200, "success":True, "error":"", "total_records":total_records, "data":ppm_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


def ppm_list_filters_codition(data):
    conditions = "1=1"
    if data.get("status"):
        conditions += " and status = '{0}'".format(data.get('status'))
    return conditions

@frappe.whitelist()
def amc_scheduling_details():
	data = json.loads(frappe.request.data)
	customer, region, city, facility=user_access_details(data.get("username"))	
	try:
		amc_schedule = frappe.db.sql("""SELECT name as amc_scheduling_id, asset_id, asset_name, asset_code, serial_number, status, amc_type, amc_val, amc_periodicity, email_id, amc_start_date, amc_end_date, customer, facility, region, city, amc_scope, vendor_name, vendor_phone, vendor_email From `tabAMC Scheduling` where customer in ({1}) and facility in ({2}) and city in ({3}) and region in ({4}) and name='{0}'""".format(data.get("amc_scheduling_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		return {"status":200, "success":True, "error":"", "data":amc_schedule}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def update_amc_scheduling():
	data = json.loads(frappe.request.data)
	try:
		if frappe.db.get_value("AMC Scheduling", {"name":data.get("amc_scheduling_id")}, "name"):
			amc_schedule = frappe.get_doc("AMC Scheduling", {"name":data.get("amc_scheduling_id")})
			amc_schedule.asset_id = data.get("asset_id")
			amc_schedule.asset_name = data.get("asset_name")
			amc_schedule.asset_code = data.get("asset_code")
			amc_schedule.serial_number = data.get("serial_number")
			amc_schedule.status = data.get("status")
			amc_schedule.amc_type = data.get("amc_type")
			amc_schedule.amc_val = data.get("amc_val")
			amc_schedule.amc_periodicity = data.get("amc_periodicity")
			amc_schedule.email_id = data.get("email_id")
			amc_schedule.amc_start_date = data.get("amc_start_date")
			amc_schedule.amc_end_date = data.get("amc_end_date")
			amc_schedule.customer = data.get("customer")
			amc_schedule.facility = data.get("facility")
			amc_schedule.region = data.get("region")
			amc_schedule.city = data.get("city")
			amc_schedule.vendor_name = data.get("vendor_name")
			amc_schedule.vendor_phone = data.get("vendor_phone")
			amc_schedule.vendor_email = data.get("vendor_email")
			amc_schedule.save(ignore_permissions=True)
			frappe.db.commit()
			return {"status_code":200, "success":True, "error":"", "data":amc_schedule}
		else:
			return {"status_code":200, "success":True, "error":"", "data":[]}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

#Get all ppm_scheduling
@frappe.whitelist()
def get_amc_scheduling_details():
	data = json.loads(frappe.request.data)
	offset = (cint(data.get("limit"))*cint(data.get("offSet"))) - cint(data.get("limit"))	
	if offset < 0 or data.get("name"):
		offset = 0

	customer, region, city, facility=user_access_details(data.get("username"))
	
	try:
		amc_details = frappe.db.sql("""SELECT name as amc_scheduling_id, asset_id, asset_name, asset_code, serial_number, status, amc_type, amc_val, amc_periodicity, email_id, amc_start_date, amc_end_date, customer, facility, region, city, amc_scope, vendor_name, vendor_phone, vendor_email From `tabAMC Scheduling` where customer in ({3}) and facility in ({4}) and city in ({5}) and region in ({6}) and {0} order by modified desc limit {1} offSet {2} """.format(get_amc_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":amc_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

def get_amc_filters_codition(data):
    conditions = "1=1"
    if data.get("amc_scheduling_id"):
        conditions += " and name = '{0}'".format(data.get('amc_scheduling_id'))
    if data.get("status"):
        conditions += " and status = '{0}'".format(data.get('status'))
    return conditions

@frappe.whitelist()
def get_amc_scheduling_list():
	data = json.loads(frappe.request.data)
	offset = (cint(data.get("limit"))*cint(data.get("offSet"))) - cint(data.get("limit"))	
	if offset < 0 or data.get("name"):
		offset = 0

	customer, region, city, facility=user_access_details(data.get("username"))

	try:
		amc_details = frappe.db.sql("""SELECT name as amc_scheduling_id, status, amc_start_date, amc_end_date From `tabAMC Scheduling` where customer in ({3}) and facility in ({4}) and city in ({5}) and region in ({6}) and {0} order by modified desc limit {1} offSet {2} """.format(amc_list_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		if not amc_details:
			amc_details = frappe.db.sql("""SELECT name as amc_scheduling_id, status, amc_start_date, amc_end_date From `tabAMC Scheduling` where customer in ({3}) and facility in ({4}) and city in ({5}) and region in ({6}) and {0} order by modified desc limit {1} offSet {2} """.format(amc_list_filters_codition(data),cint(data.get("limit")), offset, ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		total_records = len(frappe.get_all('AMC Scheduling'))
		return {"status_code":200, "success":True, "error":"", "total_records":total_records, "data":amc_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


def amc_list_filters_codition(data):
    conditions = "1=1"
    if data.get("status"):
        conditions += " and status = '{0}'".format(data.get('status'))
    return conditions


@frappe.whitelist()
def breakdown_details():
	data = json.loads(frappe.request.data)

	customer, region, city, facility=user_access_details(data.get("username"))	

	try:
		breakdown = frappe.db.sql("""SELECT name as breakdown_id, asset_id, asset_name, asset_code, serial_number, status, email_id, breakdown_time, repair_time, repaired_by, informed_to, breakdown_details, corrective_action, cumulative_downtime, amount_incurred, material_cost, labour_cost, consumable_cost, miscellaneous_cost, vendor_name, vendor_contact, vendor_email, customer, facility, region, city  From `tabBreakdown` where customer in ({1}) and facility in ({2}) and city in ({3}) and region in ({4}) and name='{0}'""".format(data.get("breakdown_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":breakdown}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def update_breakdown_details():
	data = json.loads(frappe.request.data)
	try:
		if frappe.db.get_value("Breakdown", {"name":data.get("breakdown_id")}, "name"):
			breakdown = frappe.get_doc("Breakdown", {"name":data.get("breakdown_id")})
			breakdown.asset_id = data.get("asset_id")
			breakdown.asset_code = data.get("asset_code")
			breakdown.asset_name = data.get("asset_name")
			breakdown.serial_number = data.get("serial_number")
			breakdown.status = data.get("status")
			breakdown.email_id = data.get("email_id")
			breakdown.breakdown_time = data.get("breakdown_time")
			breakdown.repair_time = data.get("repair_time")
			breakdown.repaired_by = data.get("repaired_by")
			breakdown.informed_to = data.get("informed_to")
			breakdown.vendor_name = data.get("vendor_name")
			breakdown.vendor_email = data.get("vendor_email")
			breakdown.vendor_contact = data.get("vendor_contact")
			breakdown.breakdown_details = data.get("breakdown_details")
			breakdown.corrective_action = data.get("corrective_action")
			breakdown.cumulative_downtime = data.get("cumulative_downtime")
			breakdown.amount_incurred = data.get("amount_incurred")
			breakdown.material_cost = data.get("material_cost")
			breakdown.labour_cost = data.get("labour_cost")
			breakdown.consumable_cost = data.get("consumable_cost")
			breakdown.miscellaneous_cost = data.get("miscellaneous_cost")
			breakdown.customer = data.get("customer")
			breakdown.facility = data.get("facility")
			breakdown.region = data.get("region")
			breakdown.city = data.get("city")
			breakdown.save(ignore_permissions=True)
			frappe.db.commit()
			return {"status_code":200, "success":True, "error":"", "data":breakdown}
		else:
			return {"status_code":200, "success":True, "error":"", "data":[]}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def details_of_amc_scheduling():
	data = json.loads(frappe.request.data)

	customer, region, city, facility=user_access_details(data.get("username"))

	try:
		amc_data = frappe.db.sql("""SELECT a.asset_id, a.asset_code, a.asset_name, a.serial_number, b.name as schedule_id, b.parent as amc_schedule_id, b.amc_date, b.status, b.amc_done_on, b.amc_scope, b.amc_comments, b.amc_feedback, b.amc_rating, b.material_cost, b.consumable_cost, b.labour_cost, b.miscellaneous_cost, b.device_functioning From `tabAMC Scheduling` a left join `tabAMC Schedule` b on a.name=b.parent where b.status in ('Pending', 'In Progress') and a.customer in ({1}) and a.facility in ({2}) and a.city in ({3}) and a.region in ({4}) and a.asset_id='{0}' order by b.amc_date """.format(data.get("asset_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)

		amc_details = amc_data[0] if amc_data  else []
		return {"status_code":200, "success":True, "error":"", "data":amc_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def update_detail_of_acm_scheduling():
	data = json.loads(frappe.request.data)
	try:
		frappe.db.set_value('AMC Schedule', data.get("schedule_id"), {'amc_date':data.get("amc_date"), "status":data.get("status"), "amc_done_on":data.get("amc_done_on"), "amc_scope":data.get("amc_scope"), "amc_comments":data.get("amc_comments"), "amc_feedback":data.get("amc_feedback"), "amc_rating":data.get("amc_rating"), "material_cost":data.get("material_cost"), "consumable_cost":data.get("consumable_cost"), "labour_cost":data.get("labour_cost"), "miscellaneous_cost":data.get("miscellaneous_cost"), "device_functioning":data.get("device_functioning")})
		frappe.db.commit()
		return {"status_code":200, "success":True, "error":"", "data":data}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def details_of_ppm_scheduling():
	data = json.loads(frappe.request.data)
	customer, region, city, facility=user_access_details(data.get("username"))
	try:
		ppm_data = frappe.db.sql("""SELECT a.asset_id, a.asset_code, a.asset_name, a.serial_number, b.name as schedule_id, b.parent as ppm_schedule_id, b.status, b.amc_date as ppm_date, b.ppm_periodicity, b.ppm_activity, b.ppm_comments, b.device_functioning, b.ppm_feedback, b.amc_rating as ppm_rating, b.material_cost, b.consumable_cost, b.labour_cost, b.miscellaneous_cost From `tabPPM Scheduling` a left join `tabPPM Schedule` b on a.name=b.parent where a.customer in ({2}) and a.facility in ({3}) and a.city in ({4}) and a.region in ({5}) and b.amc_date>='{1}' and a.asset_id='{0}' order by b.amc_date """.format(data.get("asset_id"), today(), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)

		ppm_details = ppm_data[0] if ppm_data  else []
		return {"status_code":200, "success":True, "error":"", "data":ppm_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def update_detail_of_ppm_scheduling():
	data = json.loads(frappe.request.data)
	try:
		frappe.db.set_value('PPM Schedule', data.get("schedule_id"), {'amc_date':data.get("ppm_date"),
			"ppm_periodicity":data.get("ppm_periodicity"), "ppm_activity":data.get("ppm_activity"), "ppm_comments":data.get("ppm_comments"), "ppm_feedback":data.get("ppm_feedback"), "amc_rating":data.get("ppm_rating"), "material_cost":data.get("material_cost"), "consumable_cost":data.get("consumable_cost"), "labour_cost":data.get("labour_cost"), "miscellaneous_cost":data.get("miscellaneous_cost"), "device_functioning":data.get("device_functioning")})
		frappe.db.commit()
		return {"status_code":200, "success":True, "error":"", "data":data}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def details_of_breakdown():
	data = json.loads(frappe.request.data)

	customer, region, city, facility=user_access_details(data.get("username"))

	try:
		breakdown = frappe.db.sql("""SELECT name as breakdown_id, asset_id, asset_name, asset_code, serial_number, status, email_id, breakdown_time, repair_time, repaired_by, informed_to, breakdown_details, corrective_action, cumulative_downtime, amount_incurred, material_cost, labour_cost, consumable_cost, miscellaneous_cost, vendor_name, vendor_contact, vendor_email, customer, facility, region, city  From `tabBreakdown` where status in ("Pending", "WIP", "Waiting for resources") and asset_id='{0}' and customer in ({1}) and facility in ({2}) and city in ({3}) and region in ({4}) """.format(data.get("asset_id"), ','.join(customer), ','.join(facility), ','.join(city), ','.join(region)), as_dict=1)
		breakdown_details = breakdown[0] if breakdown  else []
		return {"status_code":200, "success":True, "error":"", "data":breakdown_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

#---------------------------HelpDesk Section-----------------------
@frappe.whitelist()
def get_all_tickets_data():
	data = json.loads(frappe.request.data)
	city = frappe.db.sql("""select city from `tabCity Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	region = frappe.db.sql("""select region from `tabRegion Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	facility = frappe.db.sql("""select facility_addr from `tabFacility Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)

	if region:
		region = "(" + ",".join([ "'{0}'".format(item.get('region')) for item in \
		region ]) + ")"
	
	if city:
		city = "(" + ",".join([ "'{0}'".format(item.get('city')) for item in \
		city ]) + ")"

	if facility:
		facility = "(" + ",".join([ "'{0}'".format(item.get('facility_addr')) for item in \
		facility ]) + ")"

	conditions = "and 1 = 1"
	if data.get("username") and "Technician" in frappe.get_roles(data.get("username")) and data.get("username") != "Administrator":
		conditions += " and assigned_to = '{0}'".format(data.get("username"))
	if data.get("username") and "HelpDesk User" in frappe.get_roles(data.get("username")) and data.get("username") != "Administrator":
		conditions += " and email = '{0}'".format(data.get("username"))
	if data.get('search_value'):
		conditions += " and name like '%{0}%' or user_name like '%{0}%' or status like '%{0}%'".format(data.get('search_value'))
	if region:
		conditions += " and region in {0}".format(region)
	if city:
		conditions += " and city in {0}".format(city)
	if facility:
		conditions += " and facility in {0}".format(facility)

	try:
		ticket_details = frappe.db.sql(""" 
		select
			name,user,user_name,email,region,city,service_type,
			service_sub_type,building,remark,subject,area,
			facility,please_tell_us_if_you_are_satisfied as satisfaction,
			please_leave_us_feedback as rating,feedback,priority,expected_closure,
			assigned_to,status,resolution_details,asset_id,asset_name,asset_code,
			breakdown_id,amc_id,ppm_id,problem_since,location,location_details,ta_time,last_updated_on
		from
			`tabTicket`
		where 
			docstatus != 2 {0}
			order by modified desc """.format(conditions),as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":ticket_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def get_all_tasks_data():
	try:
		task_details = frappe.db.sql(""" 
		select
			name,task,details,subject,task_status,priority,type_of_task
			remarks,building,city,facility,assignee,closure_date,ticket_reference,task_resolution_date
		from
			`tabTask`
		where 
			docstatus != 2 order by modified desc """,as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":task_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def get_masters():
	data = json.loads(frappe.request.data)
	try:
		masters_dict = {}
		customer_data = frappe.db.sql(""" select customer from `tabCustomer Details` where parent = '{0}' """.format(data.get('user_id')),as_dict=1)
		city_data = frappe.db.sql(""" select city from `tabCity Details` where parent = '{0}' """.format(data.get('user_id')),as_dict=1)
		region_data = frappe.db.sql(""" select region from `tabRegion Details` where parent = '{0}' """.format(data.get('user_id')),as_dict=1)
		facility_data = frappe.db.sql(""" select facility_addr from `tabFacility Details` where parent = '{0}' """.format(data.get('user_id')),as_dict=1)
		service_type_data = frappe.db.sql(""" select name from `tabService Type` """,as_dict=1)
		service_sub_type_data = frappe.db.sql(""" select name,service_type,tat from `tabService Sub Type` """,as_dict=1)
		masters_dict.update({"customer_data":customer_data,"city_data":city_data,"region_data":region_data,"facility_data":facility_data, "service_sub_type_data":service_sub_type_data,"service_type_data":service_type_data})
		return {"status_code":200, "success":True, "error":"", "data":masters_dict}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def get_user_details():
	data = json.loads(frappe.request.data)
	conditions = "and 1 = 1"
	if data.get('search_value'):
		conditions += " and name like '%{0}%' or user_name like '%{0}%' or user_email like '%{0}%'".format(data.get('search_value'))

	try:
		user_details = frappe.db.sql(""" 
			select 
				name,user_name,user_email,area,building,location
			from
				`tabUser Details`
			where
				docstatus != 2 {0} order by creation desc """.format(conditions),as_dict=1)

		for row in user_details:
			row.update({"city_details":frappe.db.sql("select city from `tabCity Details` where parent = '{0}' ".format(row.name)),
				"customer_details":frappe.db.sql("select customer from `tabCustomer Details` where parent = '{0}' ".format(row.name)),
				"region_details":frappe.db.sql("select region from `tabRegion Details` where parent = '{0}' ".format(row.name)),
				"facility_details":frappe.db.sql("select facility from `tabFacility Details` where parent = '{0}' ".format(row.name))})
		return {"status_code":200, "success":True, "error":"", "data":user_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def create_ticket(data=None):
	try:
		data = json.loads(frappe.request.data)
		ticket_doc = frappe.new_doc("Ticket")
		ticket_doc.update(data)
		ticket_doc.flags.is_api = True
		ticket_doc.flags.ignore_permissions = True
		ticket_doc.save()
		return {"status_code":200, "success":True, "error":"", "data":ticket_doc.name, "message": "Ticket created Successfully"}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def update_ticket(data=None):
	try:
		data = json.loads(frappe.request.data)
		if frappe.get_value("Ticket",data.get("name"),"name"):
			ticket_doc = frappe.get_doc("Ticket",data.get("name"))
			ticket_doc.update(data)
			ticket_doc.flags.ignore_permissions = True
			ticket_doc.flags.is_api = True
			ticket_doc.save()
		return {"status_code":200, "success":True, "error":"", "data":data.get("name"), "message": "Ticket updated Successfully"}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def create_task(data=None):
	try:
		data = json.loads(frappe.request.data)
		task_doc = frappe.new_doc("Task")
		task_doc.update(data)
		task_doc.flags.ignore_permissions = True
		task_doc.save()
		return {"status_code":200, "success":True, "error":"", "data":task_doc.name, "message": "Task created Successfully"}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def update_task(data=None):
	try:
		data = json.loads(frappe.request.data)
		if frappe.get_value("Task",data.get("name"),"name"):
			task_doc = frappe.get_doc("Task",data.get("name"))
			task_doc.update(data)
			task_doc.flags.ignore_permissions = True
			task_doc.save()
		return {"status_code":200, "success":True, "error":"", "data":data.get("name"), "message": "Task updated Successfully"}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def asset_sub_category():
	data = json.loads(frappe.request.data)
	try:
		sub_category = frappe.db.sql("""SELECT sub_category_name From `tabAsset Sub Category` where {0} order by name """.format(asset_sub_category_filters_codition(data)), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":sub_category}		
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

def asset_sub_category_filters_codition(data):
    conditions = "1=1"
    if data.get("category"):
        conditions += " and category = '{0}'".format(data.get('category'))
    return conditions

@frappe.whitelist()
def facility_list():
	data = json.loads(frappe.request.data)
	try:
		sub_category = frappe.db.sql("""SELECT parent as facility From `tabDynamic Link` where {0} order by name """.format(facility_list_filters_codition(data)), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":sub_category}		
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

def facility_list_filters_codition(data):
    conditions = "1=1"
    if data.get("customer"):
        conditions += " and link_name = '{0}'".format(data.get('customer'))
    return conditions

@frappe.whitelist()
def get_technicians():
	data = json.loads(frappe.request.data)
	conditions = "and 1 = 1"
	if data.get('search_value'):
		conditions += " and ud.name like '%{0}%' or ud.user_name like '%{0}%' or ud.user_email like '%{0}%'".format(data.get('search_value'))

	try:
		user_details = frappe.db.sql(""" 
			select 
				ud.name,ud.user_name,ud.user_email,ud.area,ud.building,ud.location
			from
				`tabUser Details` as ud, `tabUser Roles` as ur
			where
				ud.name = ur.parent and ur.role = 'Technician'
				and ud.docstatus != 2 {0} order by ud.creation desc """.format(conditions),as_dict=1)

		for row in user_details:
			row.update({"city_details":frappe.db.sql("select city from `tabCity Details` where parent = '{0}' ".format(row.name)),
				"customer_details":frappe.db.sql("select customer from `tabCustomer Details` where parent = '{0}' ".format(row.name)),
				"region_details":frappe.db.sql("select region from `tabRegion Details` where parent = '{0}' ".format(row.name)),
				"facility_details":frappe.db.sql("select facility from `tabFacility Details` where parent = '{0}' ".format(row.name))})
		return {"status_code":200, "success":True, "error":"", "data":user_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

#=================================VMS=======================================

@frappe.whitelist()
def get_guest_registration_details():
	try:
		guest_registration_details = frappe.db.sql(""" 
		select
			name,name1,email,photo,mobile_number,company,
			vehicle_details,vehicle_name,remarks
		from
			`tabGuest Registration`
		where 
			docstatus != 2 order by creation desc """,as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":guest_registration_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def get_meeting_details():
	try:
		meeting_details = frappe.db.sql(""" 
		select
			name,meeting_id,guest,email,mobile_number,pre_approved
		from
			`tabMeeting`
		where 
			docstatus != 2 order by creation desc """,as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":meeting_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def get_meeting_master():
	try:
		meeting_master_details = frappe.db.sql(""" 
		select
			name,meeting_id,scheduled_time
		from
			`tabMeeting ID`
		where 
			docstatus != 2 order by creation desc """,as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":meeting_details}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

def user_access_details(username):
	customer=[]
	region=[]
	city=[]
	facility=[]
	user=frappe.get_doc("User Details", {"user":username})
	cust=frappe.db.sql("""select customer from `tabCustomer Details` where parent='{0}' """.format(user.name))
	reg = frappe.db.sql("""select region from `tabRegion Details` where parent='{0}' """.format(user.name))
	print(reg)
	ct = frappe.db.sql("""select city from `tabCity Details` where parent='{0}' """.format(user.name))
	flty = frappe.db.sql("""select facility_addr from `tabFacility Details` where parent='{0}' """.format(user.name))	
	for row in cust:
		customer.append(row)
	for row in reg:
		region.append(row)
	for row in ct:
		city.append(row)
	for row in flty:
		facility.append(row)

	customer = [ '"%s"'%name for name in customer ]
	region = [ '"%s"'%name for name in region ]
	city = [ '"%s"'%name for name in city ]
	facility = [ '"%s"'%name for name in facility ]
	return customer, region, city, facility

@frappe.whitelist()
def customer_list(username):
	data = json.loads(frappe.request.data)
	try:
		user=frappe.get_doc("User Details", {"user":data.get("username")})
		cust=frappe.db.sql("""select customer from `tabCustomer Details` where parent='{0}' """.format(user.name))
		return {"status_code":200, "success":True, "error":"", "data":cust}		
	except Exception as e:
		return {"status":401, "success":False, "error":e}

@frappe.whitelist()
def create_breakdown():
	data = json.loads(frappe.request.data)
	try:
		breakdown = frappe.new_doc("Breakdown")
		breakdown.asset_id = data.get("asset_id")
		breakdown.asset_code = data.get("asset_code")
		breakdown.asset_name = data.get("asset_name")
		breakdown.serial_number = data.get("serial_number")
		breakdown.status = "Pending"
		breakdown.email_id = data.get("email_id")
		breakdown.breakdown_time = now_datetime()
		breakdown.repair_time = data.get("repair_time")
		breakdown.repaired_by = data.get("repaired_by")
		breakdown.informed_to = data.get("informed_to")
		breakdown.vendor_name = data.get("vendor_name")
		breakdown.vendor_email = data.get("vendor_email")
		breakdown.vendor_contact = data.get("vendor_contact")
		breakdown.breakdown_details = data.get("breakdown_details")
		breakdown.corrective_action = data.get("corrective_action")
		breakdown.cumulative_downtime = data.get("cumulative_downtime")
		breakdown.amount_incurred = data.get("amount_incurred")
		breakdown.material_cost = data.get("material_cost")
		breakdown.labour_cost = data.get("labour_cost")
		breakdown.consumable_cost = data.get("consumable_cost")
		breakdown.miscellaneous_cost = data.get("miscellaneous_cost")
		breakdown.customer = data.get("customer")
		breakdown.facility = data.get("facility")
		breakdown.region = frappe.db.get_value("Address", {"name": data.get("facility")}, "kf_region") 
		breakdown.city = frappe.db.get_value("Address", {"name": data.get("facility")}, "kf_city")
		breakdown.creation = now_datetime()
		breakdown.owner = data.get("username")
		breakdown.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.db.set_value("Asset Register", data.get("asset_id"), "status", "Breakdown")
		return {"status_code":200, "success":True, "error":"", "data":breakdown}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}


@frappe.whitelist()
def asset_category():
	data = json.loads(frappe.request.data)
	search = '%'+data.get("search")+'%'
	try:
		asset_category=frappe.db.sql("""select name as category from `tabAssets Category` where name like '{0}' """.format(search), as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":asset_category}		
	except Exception as e:
		return {"status":401, "success":False, "error":e}

@frappe.whitelist()
def get_amc_list():
	data = json.loads(frappe.request.data)
	city = frappe.db.sql("""select city from `tabCity Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	region = frappe.db.sql("""select region from `tabRegion Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	facility = frappe.db.sql("""select facility_addr from `tabFacility Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	customer = frappe.db.sql("""select customer from `tabCustomer Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)

	if region:
		region = "(" + ",".join([ "'{0}'".format(item.get('region')) for item in \
		region ]) + ")"
	
	if city:
		city = "(" + ",".join([ "'{0}'".format(item.get('city')) for item in \
		city ]) + ")"

	if facility:
		facility = "(" + ",".join([ "'{0}'".format(item.get('facility_addr')) for item in \
		facility ]) + ")"

	if customer:
		customer = "(" + ",".join([ "'{0}'".format(item.get('customer')) for item in \
		customer ]) + ")"

	conditions = "1 = 1"
	if region:
		conditions += " and region in {0}".format(region)
	if city:
		conditions += " and city in {0}".format(city)
	if facility:
		conditions += " and facility in {0}".format(facility)
	if customer:
		conditions += " and customer in {0}".format(customer)
	if data.get('search_value'):
		conditions += " and name like '%{0}%' ".format(data.get('search_value'))
	try:
		amc_data = frappe.db.sql(""" select name from `tabAMC Scheduling` where {0} """.format(conditions),as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":amc_data}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def get_ppm_list():
	data = json.loads(frappe.request.data)
	city = frappe.db.sql("""select city from `tabCity Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	region = frappe.db.sql("""select region from `tabRegion Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	facility = frappe.db.sql("""select facility_addr from `tabFacility Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	customer = frappe.db.sql("""select customer from `tabCustomer Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)

	if region:
		region = "(" + ",".join([ "'{0}'".format(item.get('region')) for item in \
		region ]) + ")"
	
	if city:
		city = "(" + ",".join([ "'{0}'".format(item.get('city')) for item in \
		city ]) + ")"

	if facility:
		facility = "(" + ",".join([ "'{0}'".format(item.get('facility_addr')) for item in \
		facility ]) + ")"

	if customer:
		customer = "(" + ",".join([ "'{0}'".format(item.get('customer')) for item in \
		customer ]) + ")"

	conditions = "1 = 1"

	if region:
		conditions += " and region in {0}".format(region)
	if city:
		conditions += " and city in {0}".format(city)
	if facility:
		conditions += " and facility in {0}".format(facility)
	if customer:
		conditions += " and customer in {0}".format(customer)
	if data.get('search_value'):
		conditions += " and name like '%{0}%' ".format(data.get('search_value'))
	
	try:
		ppm_data = frappe.db.sql(""" select name from `tabPPM Scheduling` where {0} """.format(conditions),as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":ppm_data}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}

@frappe.whitelist()
def get_breakdown_list():
	data = json.loads(frappe.request.data)
	city = frappe.db.sql("""select city from `tabCity Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	region = frappe.db.sql("""select region from `tabRegion Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	facility = frappe.db.sql("""select facility_addr from `tabFacility Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)
	customer = frappe.db.sql("""select customer from `tabCustomer Details` where parent='{0}' """.format(data.get("user_id")),as_dict=1)

	if region:
		region = "(" + ",".join([ "'{0}'".format(item.get('region')) for item in \
		region ]) + ")"
	
	if city:
		city = "(" + ",".join([ "'{0}'".format(item.get('city')) for item in \
		city ]) + ")"

	if facility:
		facility = "(" + ",".join([ "'{0}'".format(item.get('facility_addr')) for item in \
		facility ]) + ")"

	if customer:
		customer = "(" + ",".join([ "'{0}'".format(item.get('customer')) for item in \
		customer ]) + ")"

	conditions = "1 = 1"
	if region:
		conditions += " and region in {0}".format(region)
	if city:
		conditions += " and city in {0}".format(city)
	if facility:
		conditions += " and facility in {0}".format(facility)
	if customer:
		conditions += " and customer in {0}".format(customer)
	if data.get('search_value'):
		conditions += " and name like '%{0}%' ".format(data.get('search_value'))
	
	try:
		breakdown_data = frappe.db.sql(""" select name from `tabBreakdown` where {0} """.format(conditions),as_dict=1)
		return {"status_code":200, "success":True, "error":"", "data":breakdown_data}
	except Exception as e:
		return {"status_code":401, "success":False, "error":e}