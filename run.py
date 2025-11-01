#!/usr/bin/env python3
"""
Simple runner script for risk assessment.
Usage: python run.py --software "Software Name" --company "Company Name"
"""

import sys
from risk_assessment.main import app

if __name__ == "__main__":
    app()

