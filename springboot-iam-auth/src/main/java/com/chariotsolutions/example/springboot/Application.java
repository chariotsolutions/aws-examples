package com.chariotsolutions.example.springboot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.context.annotation.Bean;

import com.zaxxer.hikari.HikariDataSource;


@SpringBootApplication
public class Application
{
    public static void main(String[] args)
    {	
        SpringApplication.run(Application.class, args);
    }
	

    @Bean
    @ConfigurationProperties(prefix = "spring.datasource")
    public HikariDataSource dataSource()
    {
        HikariDataSource ds = DataSourceBuilder.create().type(HikariDataSource.class).build();
        return ds;
    }
}
