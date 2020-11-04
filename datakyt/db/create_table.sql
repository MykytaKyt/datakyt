SET ROLE datakyt_admin;

-- Table description
CREATE TABLE project
(
	id	        SMALLSERIAL 	PRIMARY KEY,
	name		char(65)	    NOT NULL

);


CREATE TABLE office
(
	id	        SMALLSERIAL 	PRIMARY KEY,
	city		char(255)	    NOT NULL

);


CREATE TABLE employee
(
	id		SMALLSERIAL 	PRIMARY KEY,
	name		char(65)	NOT NULL,
	email		char(65) 	UNIQUE,
	phone		varchar(65)	UNIQUE,
	project_id	SMALLSERIAL
	    CONSTRAINT project_id_fk REFERENCES project (id) ON DELETE CASCADE,
	office_id	SMALLSERIAL
	    CONSTRAINT office_id_fk REFERENCES office (id) ON DELETE CASCADE


);

CREATE TABLE equipment_type
(
	id	SMALLSERIAL 	PRIMARY KEY,
	name			char(255)	UNIQUE

);

CREATE TABLE equipment
(
	id			        SMALLSERIAL 	PRIMARY KEY,
	name			    char(255)	NOT NULL,
	warranty		    integer		NOT NULL,
	cost			    money    	NOT NULL CHECK (cost > 0::money),
	status			    varchar(65)	NOT NULL
            CONSTRAINT status_check CHECK(status IN('issued','on reserve','in repair','broken')),
	description		    char(255),
	purchase_date		date 		NOT NULL,
	serial_number	    varchar(65)		NOT NULL,
	equipment_type_id	SMALLSERIAL
	    CONSTRAINT equipment_type_id_fk REFERENCES equipment_type(id) ON DELETE CASCADE


);



CREATE TABLE equipment_part
(
	id	            SMALLSERIAL 	PRIMARY KEY,
	name			char(255)	    UNIQUE,
	equipment_id	SMALLSERIAL
	    CONSTRAINT equipment_id_fk REFERENCES equipment(id) ON DELETE CASCADE

);

CREATE TABLE software
(
	id	SMALLSERIAL	PRIMARY KEY,
	name	text		NOT NULL

);

CREATE TABLE software_license
(
	id		            SMALLSERIAL	PRIMARY KEY,
	software_id	        SMALLSERIAL
	    CONSTRAINT software_id_fk REFERENCES software(id) ON DELETE CASCADE,
	product_key	        text		UNIQUE,
	date_of_purchase	date		NOT NULL,
	date_of_expiry	    date		NOT NULL


);

CREATE TABLE employee_sw_license
(
	id			        SMALLSERIAL 	PRIMARY KEY,
	date_of_issue		date		NOT NULL,
	date_of_return		date,
	employee_id		    SMALLSERIAL
	    CONSTRAINT employee_id_fk REFERENCES employee(id) ON DELETE CASCADE,
	software_license_id	SMALLSERIAL
	    CONSTRAINT software_license_id_fk REFERENCES software_license(id) ON DELETE CASCADE

);



CREATE TABLE furniture_type
(
	id	SMALLSERIAL 	PRIMARY KEY,
	type	text	UNIQUE

);

CREATE TABLE furniture
(
	id			        SMALLSERIAL	PRIMARY KEY,
	furniture_type_id	SMALLSERIAL
	    CONSTRAINT furniture_type_id_fk REFERENCES furniture_type (id) ON DELETE CASCADE,
	name			    text		NOT NULL,
	warranty			integer		NOT NULL,
	cost			    money 	NOT NULL CHECK (cost > 0::money)

);

CREATE TABLE employee_furniture
(

	id		        SMALLSERIAL 	PRIMARY KEY,
	date_of_issue	date		    NOT NULL,
	furniture_id	SMALLSERIAL
	    CONSTRAINT furniture_id_fk REFERENCES furniture (id) ON DELETE CASCADE,
	employee_id	    SMALLSERIAL
	    CONSTRAINT employee_id_fk REFERENCES employee (id) ON DELETE CASCADE


);

CREATE TABLE employee_equipment
(
	id			        SMALLSERIAL 	PRIMARY KEY,
	employee_id		    SMALLSERIAL
	    CONSTRAINT employee_id_fk REFERENCES employee(id) ON DELETE CASCADE,
	equipment_id		SMALLSERIAL
	    CONSTRAINT equipment_id_fk REFERENCES equipment(id) ON DELETE CASCADE,
	date_of_issue		date		NOT NULL,
	day_of_return		date

);




-- DROP TABLE  employee, office, project, employee_equipment, employee_furniture,
--     furniture, furniture_type, employee_sw_license, software_license, software,
--     equipment_part, equipment, equipment_type;


