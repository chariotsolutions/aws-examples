#!/usr/bin/env node
import 'source-map-support/register';
import cdk = require('@aws-cdk/core');

import { UsersAndGroupsStack } from '../lib/stack';

const app = new cdk.App();
new UsersAndGroupsStack(app, 'UsersAndGroupsStack');
