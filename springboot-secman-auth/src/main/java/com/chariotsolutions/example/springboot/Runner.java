package com.chariotsolutions.example.springboot;

import java.sql.Timestamp;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;


/**
 *  This class performs the actual retrieval operation. It is invoked by the 
 *  application main.
 */
@Component
public class Runner
implements CommandLineRunner
{
    private Logger logger = LoggerFactory.getLogger(getClass());

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(String... args) throws Exception
    {
        logger.info("application started");

        Timestamp jdbcUser = jdbcTemplate.queryForObject("select current_timestamp", Timestamp.class);
        logger.info("database timestamp: {}", jdbcUser);
    }

}
