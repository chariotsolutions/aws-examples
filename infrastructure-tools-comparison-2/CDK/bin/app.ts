#!/usr/bin/env node
import 'source-map-support/register';
import cdk = require('@aws-cdk/core');

import { MultiQueueStack } from '../lib/stack';

const app = new cdk.App();
new MultiQueueStack(app, 'MultiQueueStack');
