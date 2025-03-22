#!/usr/bin/env python3
"""
Script to add additional CS modules to the database.
This expands the range of modules available for content recommendations.
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('add_modules')

# Make sure we can import from the application
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

try:
    # Import application components
    from config import MONGO_URI, MONGO_DB_NAME
    from pymongo import MongoClient
    
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    modules_collection = db.modules
    
    def add_modules(new_modules):
        """Add new modules to the database, avoiding duplicates by code
        
        Args:
            new_modules: List of module dictionaries
            
        Returns:
            tuple: (number of modules added, number of modules skipped)
        """
        added = 0
        skipped = 0
        
        for module in new_modules:
            # Check if module with this code already exists
            existing = modules_collection.find_one({"code": module["code"]})
            
            if existing:
                logger.info(f"Module '{module['name']}' ({module['code']}) already exists, skipping")
                skipped += 1
                continue
                
            # Add timestamps
            module["created_at"] = datetime.now()
            module["updated_at"] = datetime.now()
            module["vector_embedding"] = None  # Will be populated by embedding service
            
            # Insert new module
            result = modules_collection.insert_one(module)
            
            if result.inserted_id:
                logger.info(f"Added module: {module['name']} ({module['code']})")
                added += 1
            
        return added, skipped
    
    def main():
        """Main function to run the script"""
        logger.info("Starting to add CS modules")
        
        # Define additional CS modules to add
        # ADD YOUR MODULE DEFINITIONS HERE
        # Each module should be a dictionary with name, code, description, and keywords
        new_modules = [

            {
                "name": "Introduction to Computer Science",
                "code": "COMP 110",
                "description": "An overview of computer science, covering fundamental concepts, problem-solving techniques, hardware, software, and the impact of computing on society.",
                "keywords": ["computer science", "problem-solving", "hardware", "software", "computing"]
            },
            {
                "name": "Fundamentals of Programming",
                "code": "COMP 112",
                "description": "Introduction to programming concepts, including variables, control structures, functions, and basic algorithms.",
                "keywords": ["programming", "variables", "control structures", "functions", "algorithms"]
            },
            {
                "name": "Structured Programming",
                "code": "COMP 120",
                "description": "Covers principles of structured programming, including modular design, loops, conditionals, and error handling.",
                "keywords": ["structured programming", "modular design", "loops", "conditionals", "error handling"]
            },
            {
                "name": "Introduction to Programming",
                "code": "COMP 121",
                "description": "Basic programming techniques using a high-level language, covering syntax, data types, and control structures.",
                "keywords": ["programming", "syntax", "data types", "control structures", "high-level language"]
            },
            {
                "name": "Database Management Systems 1",
                "code": "COMP 124",
                "description": "Introduction to databases, covering relational database concepts, SQL, and basic database design.",
                "keywords": ["database", "SQL", "relational databases", "data modeling", "database design"]
            },
            {
                "name": "Database Management Systems 2",
                "code": "COMP 324",
                "description": "Advanced database concepts including normalization, indexing, transaction management, and distributed databases.",
                "keywords": ["advanced databases", "normalization", "indexing", "transactions", "distributed databases"]
            },
            {
                "name": "Web Applications Programming",
                "code": "COMP 310",
                "description": "Development of dynamic web applications using frontend and backend technologies, databases, and web frameworks.",
                "keywords": ["web development", "frontend", "backend", "databases", "frameworks"]
            },
            {
                "name": "Mobile Computing",
                "code": "COMP 340",
                "description": "Study of mobile systems, application development, networking, and optimization for mobile devices.",
                "keywords": ["mobile computing", "app development", "networking", "optimization", "wireless"]
            },
            {
                "name": "Software Engineering",
                "code": "COMP 313",
                "description": "Principles of software development, covering software lifecycle, requirements engineering, design patterns, and testing.",
                "keywords": ["software development", "lifecycle", "design patterns", "testing", "engineering"]
            },
            {
                "name": "Design and Analysis of Algorithms",
                "code": "COMP 311",
                "description": "Study of algorithm efficiency, complexity analysis, and design paradigms such as divide and conquer, dynamic programming, and greedy algorithms.",
                "keywords": ["algorithms", "complexity", "divide and conquer", "dynamic programming", "greedy algorithms"]
            },
            {
                "name": "Distributed Systems",
                "code": "COMP 322",
                "description": "Fundamentals of distributed computing, covering communication, synchronization, fault tolerance, and distributed storage.",
                "keywords": ["distributed computing", "communication", "synchronization", "fault tolerance", "storage"]
            },
            {
                "name": "Object-Oriented Analysis and Design",
                "code": "COMP 320",
                "description": "Techniques for analyzing and designing software using object-oriented methodologies, UML diagrams, and design patterns.",
                "keywords": ["OOP", "analysis", "design", "UML", "design patterns"]
            },
            {
                "name": "Computer Networks",
                "code": "COMP 312",
                "description": "Concepts of computer networking, including protocols, network architectures, security, and data communication.",
                "keywords": ["computer networks", "protocols", "security", "data communication", "network architecture"]
            },
            {
                "name": "Assembly Language Programming",
                "code": "COMP 225",
                "description": "Introduction to low-level programming using assembly language, covering instruction sets, memory management, and optimization techniques.",
                "keywords": ["assembly", "low-level programming", "instruction set", "memory management", "optimization"]
            },
            {
                "name": "Numerical Analysis 1",
                "code": "MATH 314",
                "description": "Study of numerical methods for solving mathematical problems, including interpolation, numerical differentiation, and integration.",
                "keywords": ["numerical methods", "interpolation", "differentiation", "integration", "mathematical computation"]
            },
            {
                "name": "Data Communication",
                "code": "COMP 221",
                "description": "Covers the fundamentals of data transmission, network protocols, and communication models in computer networks.",
                "keywords": ["data communication", "network protocols", "transmission", "computer networks", "communication models"]
            },
            {
                "name": "Computer Organization and Architecture",
                "code": "COMP 224",
                "description": "Study of computer hardware components, instruction set architecture, memory hierarchy, and processor design.",
                "keywords": ["computer architecture", "hardware", "memory hierarchy", "processor design", "instruction set"]
            },
            {
                "name": "Object-Oriented Programming with Java",
                "code": "COMP 226",
                "description": "Covers object-oriented programming concepts in Java, including encapsulation, inheritance, polymorphism, and exception handling.",
                "keywords": ["Java", "OOP", "encapsulation", "inheritance", "polymorphism", "exception handling"]
            },
                {
                "name": "Team Project",
                "code": "COMP 323",
                "description": "Practical application of software development skills through team-based project work.",
                "keywords": ["team project", "software development", "collaboration", "project management", "agile development"]
            },
            {
                "name": "Visual Programming",
                "code": "COMP 329",
                "description": "Introduction to graphical user interface (GUI) design and event-driven programming using modern frameworks.",
                "keywords": ["visual programming", "GUI", "event-driven programming", "frameworks", "user interfaces"]
            },
            {
                "name": "Vector Geometry",
                "code": "MATH 111",
                "description": "Covers vector algebra, dot and cross products, lines, planes, and their applications in geometry.",
                "keywords": ["vector algebra", "dot product", "cross product", "lines", "planes", "geometry"]
            },
            {
                "name": "Calculus 1",
                "code": "MATH 113",
                "description": "Introduction to differential calculus, including limits, continuity, differentiation, and applications in real-world problems.",
                "keywords": ["calculus", "limits", "continuity", "differentiation", "derivatives", "applications"]
            },
            {
                "name": "Integral Calculus",
                "code": "MATH 121",
                "description": "Focus on integration techniques, applications of definite and indefinite integrals, and computations involving area and volume.",
                "keywords": ["integration", "definite integrals", "indefinite integrals", "area computations", "volume computations"]
            },
            {
                "name": "Introduction to Probability and Statistics 1",
                "code": "MATH 123",
                "description": "Basic probability and statistical concepts, including probability distributions, data analysis, and hypothesis testing.",
                "keywords": ["probability", "statistics", "distributions", "data analysis", "hypothesis testing"]
            },
            {
                "name": "Electricity and Magnetism",
                "code": "PHYS 110",
                "description": "Covers fundamental principles of electric and magnetic fields, circuits, and electromagnetic waves.",
                "keywords": ["electric fields", "magnetism", "circuits", "electromagnetic waves", "physics"]
            },
            {
                "name": "Basic Electronics",
                "code": "PHYS 120",
                "description": "Introduction to electronic components, circuits, and basic digital and analog electronics principles.",
                "keywords": ["electronics", "circuits", "digital electronics", "analog electronics", "components"]
            },
            {
                "name": "Digital Circuit Design",
                "code": "COMP 213",
                "description": "Covers logic gates, combinational and sequential circuits, and digital system design techniques.",
                "keywords": ["logic gates", "digital circuits", "combinational logic", "sequential circuits", "circuit design"]
            },
            {
                "name": "Data Structures with C",
                "code": "COMP 214",
                "description": "Implementation of data structures such as arrays, linked lists, stacks, and queues using the C programming language.",
                "keywords": ["data structures", "C programming", "arrays", "linked lists", "stacks", "queues"]
            },
            {
                "name": "Object-Oriented Programming with C++",
                "code": "COMP 215",
                "description": "Introduction to object-oriented programming concepts in C++, including classes, objects, inheritance, and polymorphism.",
                "keywords": ["C++", "OOP", "classes", "objects", "inheritance", "polymorphism"]
            },
            {
                "name": "Operations Research",
                "code": "COMP 315",
                "description": "Covers optimization techniques, decision analysis, linear programming, and simulation methods for problem-solving in operations management.",
                "keywords": ["operations research", "optimization", "linear programming", "decision analysis", "simulation"]
            },
            {
                "name": "Differential Equations 1",
                "code": "MATH 312",
                "description": "Introduction to ordinary differential equations, including first-order and second-order equations, applications, and solution techniques.",
                "keywords": ["differential equations", "ODEs", "first-order equations", "second-order equations", "applications"]
            },
            {
                "name": "Linear Algebra 1",
                "code": "MATH 211",
                "description": "Covers fundamental concepts of linear algebra, including matrices, determinants, vector spaces, and linear transformations.",
                "keywords": ["linear algebra", "matrices", "determinants", "vector spaces", "linear transformations"]
            },

            {
            "name": "Research Project I",
            "code": "COMP 410",
            "description": "Independent research project focusing on problem identification, literature review, and proposal development in computer science.",
            "keywords": ["research", "project", "proposal", "literature review", "problem identification", "independent study", "computing"]
            },
            {
            "name": "Computer Graphics",
            "code": "COMP 411",
            "description": "Fundamentals of computer graphics, including 2D and 3D rendering, transformations, shading, and interactive applications.",
            "keywords": ["graphics", "rendering", "3D", "shading", "modeling", "animation", "visualization"]
            },
            {
            "name": "Artificial Intelligence",
            "code": "COMP 412",
            "description": "Introduction to artificial intelligence concepts such as machine learning, neural networks, expert systems, and natural language processing.",
            "keywords": ["AI", "machine learning", "neural networks", "expert systems", "NLP", "search algorithms", "automation"]
            },
            {
            "name": "Microprocessor Based Systems",
            "code": "COMP 414",
            "description": "Study of microprocessor architecture, assembly language programming, system interfacing, and embedded systems development.",
            "keywords": ["microprocessor", "assembly", "embedded systems", "architecture", "hardware", "interfacing", "low-level programming"]
            },
            {
            "name": "Client and Server Side Programming",
            "code": "COMP 441",
            "description": "Development of dynamic web applications using both client and server-side technologies, databases, and security considerations.",
            "keywords": ["web development", "client-side", "server-side", "databases", "security", "JavaScript", "API"]
            },
            {
            "name": "Internetworking with TCP/IP",
            "code": "COMP 451",
            "description": "Comprehensive study of TCP/IP networking, covering network architecture, protocols, addressing, and security mechanisms.",
            "keywords": ["networking", "TCP/IP", "protocols", "security", "addressing", "routing", "firewalls"]
            },
            {
            "name": "Advanced Web Applications Programming",
            "code": "COMP 442",
            "description": "Development of complex web applications, focusing on frameworks, security, optimization, and user experience design.",
            "keywords": ["web development", "frameworks", "security", "optimization", "UX", "JavaScript", "API"]
            },
            {
            "name": "User Interface Design",
            "code": "COMP 443",
            "description": "Principles of user interface and experience design, including usability testing, accessibility standards, and front-end frameworks.",
            "keywords": ["UI/UX", "design", "usability", "accessibility", "HCI", "interaction design", "prototyping"]
            },
            {
            "name": "Simulation and Modeling",
            "code": "COMP 452",
            "description": "Techniques for modeling and simulating real-world systems using computational tools and statistical methods.",
            "keywords": ["simulation", "modeling", "statistical methods", "computation", "probability", "optimization", "real-world applications"]
            },
            {
            "name": "Real Time Application",
            "code": "COMP 453",
            "description": "Development of real-time applications with emphasis on concurrency, performance, and time-sensitive computing.",
            "keywords": ["real-time", "concurrency", "performance", "scheduling", "parallel computing", "latency", "system design"]
            },
            {
            "name": "Professional Ethics and Information Law",
            "code": "COMP 420",
            "description": "Exploration of ethical, social, and legal issues in computing, including data privacy, cybersecurity policies, and intellectual property.",
            "keywords": ["ethics", "law", "privacy", "cybersecurity", "intellectual property", "compliance", "data protection"]
            },
            {
            "name": "Software Quality Management",
            "code": "COMP 421",
            "description": "Study of software testing, quality assurance methodologies, and risk management in software development.",
            "keywords": ["software quality", "testing", "QA", "risk management", "verification", "validation", "process improvement"]
            },
            {
            "name": "Research Project II",
            "code": "COMP 422",
            "description": "Continuation of Research Project I, emphasizing implementation, experimentation, and evaluation of research outcomes.",
            "keywords": ["research", "implementation", "experimentation", "evaluation", "results analysis", "report writing", "presentation"]
            },
            {
            "name": "Seminars in Computer Science",
            "code": "COMP 423",
            "description": "Discussions and presentations on emerging topics and advancements in computer science research and industry trends.",
            "keywords": ["seminars", "computer science", "presentations", "industry trends", "technology", "innovation", "research"]
            }
                    
                ]
        
        # Add modules to database
        added, skipped = add_modules(new_modules)
        
        logger.info(f"Module addition completed: {added} modules added, {skipped} skipped")
        client.close()
        logger.info("Database connection closed")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    logger.error("Make sure you're running this script from the project root or the correct Python environment")
    sys.exit(1)