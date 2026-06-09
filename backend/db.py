"""
Medical Database Module
Supports temporal modeling and dynamic Bayesian updates
"""

import sqlite3
from datetime import datetime
from typing import List, Optional, Dict
import json


class MedicalDatabase:
    """Database for storing patient medical history"""
    
    def __init__(self, db_path: str = "medical_reports.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                name TEXT,
                age INTEGER,
                gender TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                report_date TIMESTAMP NOT NULL,
                report_type TEXT,
                parsed_data TEXT,
                medical_summary TEXT,
                simple_explanation TEXT,
                translated_explanation TEXT,
                target_language TEXT,
                risk_probability REAL,
                suggestions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """)
        
        # Lab values table for temporal analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                patient_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                value REAL,
                unit TEXT,
                reference_range TEXT,
                status TEXT,
                report_date TIMESTAMP NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patient_reports 
            ON reports(patient_id, report_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lab_values 
            ON lab_values(patient_id, test_name, report_date)
        """)
        
        conn.commit()
        conn.close()
    
    def save_report(
        self,
        patient_id: str,
        report_date: str,
        parsed_data: str,
        summary: str,
        simple_explanation: str,
        translated: str,
        risk_probability: float,
        report_type: str = "pathological"
    ):
        """Save a medical report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert or update patient
        cursor.execute("""
            INSERT OR IGNORE INTO patients (patient_id) VALUES (?)
        """, (patient_id,))
        
        # Insert report
        cursor.execute("""
            INSERT INTO reports (
                patient_id, report_date, report_type, parsed_data,
                medical_summary, simple_explanation, translated_explanation,
                target_language, risk_probability
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id, report_date, report_type, parsed_data,
            summary, simple_explanation, translated, "Hindi",
            risk_probability
        ))
        
        report_id = cursor.lastrowid
        
        # Parse and store individual lab values
        try:
            parsed = json.loads(parsed_data)
            for lab in parsed.get("lab_values", []):
                try:
                    value = float(lab.get("value", 0))
                except:
                    value = None
                
                cursor.execute("""
                    INSERT INTO lab_values (
                        report_id, patient_id, test_name, value, unit,
                        reference_range, status, report_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_id, patient_id,
                    lab.get("test_name", ""),
                    value,
                    lab.get("unit", ""),
                    lab.get("reference_range", ""),
                    lab.get("status", "unknown"),
                    report_date
                ))
        except:
            pass  # Skip if parsing fails
        
        conn.commit()
        conn.close()
        
        return report_id
    
    def get_patient_reports(self, patient_id: str, limit: int = 10) -> List[Dict]:
        """Get patient's report history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM reports 
            WHERE patient_id = ?
            ORDER BY report_date DESC
            LIMIT ?
        """, (patient_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_lab_values_over_time(
        self, 
        patient_id: str, 
        test_name: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get historical values for a specific test"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM lab_values
            WHERE patient_id = ? AND test_name = ?
            ORDER BY report_date DESC
            LIMIT ?
        """, (patient_id, test_name, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_temporal_summary(self, patient_id: str) -> Dict:
        """Get temporal summary for a patient"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all unique tests
        cursor.execute("""
            SELECT DISTINCT test_name FROM lab_values
            WHERE patient_id = ?
        """, (patient_id,))
        
        tests = [row["test_name"] for row in cursor.fetchall()]
        
        trends = []
        for test in tests:
            cursor.execute("""
                SELECT value, status, report_date FROM lab_values
                WHERE patient_id = ? AND test_name = ?
                ORDER BY report_date DESC
                LIMIT 5
            """, (patient_id, test))
            
            values = cursor.fetchall()
            if len(values) >= 2:
                statuses = [v["status"] for v in values]
                if all(s == "low" for s in statuses):
                    trends.append({
                        "test": test,
                        "pattern": "persistently_low",
                        "count": len(values)
                    })
                elif all(s == "high" for s in statuses):
                    trends.append({
                        "test": test,
                        "pattern": "persistently_high",
                        "count": len(values)
                    })
        
        conn.close()
        
        return {
            "patient_id": patient_id,
            "unique_tests": len(tests),
            "trends": trends
        }
    
    def get_all_patients(self) -> List[Dict]:
        """Get all patients"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT patient_id, name, created_at,
            (SELECT COUNT(*) FROM reports WHERE patient_id = patients.patient_id) as report_count
            FROM patients
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]