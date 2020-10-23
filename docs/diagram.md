# Table software consist of:

var name | type    | constraints | description
-------- | ------- | ----------- | ----------------------
**id**   | PK, INT | NOT NULL    | stores id of software
**name** | TEXT    | -           | store name of software

# Table software_license consist of:

var name             | type    | constraints | description
-------------------- | ------- | ----------- | ------------------------------------------
**id**               | PK, INT | NOT NULL    | stores id of a software license
**software_id**      | FK, INT | NOT NULL    | refers to the table software
**key_product**      | TEXT    | -           | stores product key of software
**date_of_purchase** | DATE    | -           | stores info when the license was purchased
**expires_date**     | DATE    | -           | stores the expiration date of the license

# Table employee_sw_license consist of:

var name                | type    | constraints | description
----------------------- | ------- | ----------- | --------------------------------------
**id**                  | PK, INT | NOT NULL    | stores id of employee software license
**employee_id**         | FK, INT | NOT NULL    | refers to the table employee
**software_license_id** | FK, INT | NOT NULL    | refers to the table software_license
**date_of_issue**       | DATE    | -           | stores info when license was issued
**pick_up_date**        | DATE    | -           | stores info when license was picked up

# Table furniture consist of:

var name     | type    | constraints | description
------------ | ------- | ----------- | ----------------------------------
**id**       | PK, INT | NOT NULL    | stores id of furniture
**type_id**  | FK, INT | NOT NULL    | refers to the table furniture_type
**name**     | TEXT    | -           | stores name of furniture
**warranty** | INT     | -           | stores duration of warranty
**cost**     | INT     | -           | stores cost of furniture

# Table furniture_type consist of:

var name | type     | constraints | description
-------- | -------- | ----------- | -------------------------------------------
**id**   | PK, INT  | NOT NULL    | stores id of furniture types
**type** | CHAR(64) | -           | stores info of different types of furniture

# Table employee_furniture consist of:

var name          | type    | constraints | description
----------------- | ------- | ----------- | -------------------------------------
**id**            | PK, INT | NOT NULL    | stores id of employee furniture
**furniture_id**  | FK, INT | NOT NULL    | refers to the table furniture
**employee_id**   | FK, INT | NOT NULL    | refers to the table employee
**date_of_issue** | DATE    | -           | stores info when furniture was issued
