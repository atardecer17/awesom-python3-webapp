

drop database if exists awesome;
create database awesome;

use awesome;

grant select, insert, update, delete on awesome.* to 'www-data'@'localhost' identified by 'www-data';

create table users (
        id varchar(50) not null,
        email varchar(50) not null,
        passwd varchar(50) not null,
        admin bool not null,
        name VARCHAR(50) NOT NULL,
        image VARCHAR(500) NOT NULL,
        created_at REAL NOT NULL,
        UNIQUE KEY idx_email (email),
        KEY idx_created_at (created_at),
        PRIMARY KEY (id)
) engine=innodb default charset=utf8;


create table blogs(
        id VARCHAR(50) NOT NULL,
        user_id VARCHAR(50) NOT NULL,
        user_name VARCHAR(50) NOT NULL,
        user_image VARCHAR(50) NOT NULL,
        name VARCHAR(50) NOT NULL,
        summary VARCHAR(50) NOT NULL,
        content mediumtext NOT NULL,
        created_at real not null,
        KEY idx_created_at (created_at),
        PRIMARY KEY (id)    
) engine=innodb default charset=utf8;


create table comments(
        id varchar(50) not null,
        blog_id VARCHAR(50) NOT NULL,
        user_id VARCHAR(50) NOT NULL,
        user_name VARCHAR(50) NOT NULL,
        user_image VARCHAR(500) NOT NULL,
        content mediumtext NOT NULL,
        created_at real not null,
        KEY idx_created_at (created_at),
        PRIMARY KEY(id)
)engine=innodb default charset=utf8;

        





