-- AI-Solutions Flask + MySQL database
-- Import this file in phpMyAdmin while XAMPP MySQL is running.
-- Default admin: admin@ai-solutions.com / admin123

CREATE DATABASE IF NOT EXISTS ai_solutions_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_solutions_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS inquiry_replies;
DROP TABLE IF EXISTS chatbot_inquiries;
DROP TABLE IF EXISTS chatbot_messages;
DROP TABLE IF EXISTS event_registrations;
DROP TABLE IF EXISTS contact_inquiries;
DROP TABLE IF EXISTS testimonials;
DROP TABLE IF EXISTS gallery_items;
DROP TABLE IF EXISTS case_studies;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS admins;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    slug VARCHAR(170) NOT NULL UNIQUE,
    short_description VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(40) DEFAULT '🤖',
    industry VARCHAR(100) DEFAULT 'Technology',
    display_order INT DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_services_active (is_active),
    INDEX idx_services_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(220) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    author VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    content LONGTEXT NOT NULL,
    image_url VARCHAR(500),
    published_at DATE NOT NULL,
    is_featured TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_articles_active_date (is_active, published_at),
    INDEX idx_articles_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    location VARCHAR(200) NOT NULL,
    short_description VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    image_url VARCHAR(500),
    category VARCHAR(100) DEFAULT 'AI Event',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_events_date (event_date),
    INDEX idx_events_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE case_studies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    client_name VARCHAR(150) NOT NULL,
    summary TEXT NOT NULL,
    before_text TEXT,
    after_text TEXT,
    result_metric VARCHAR(180),
    image_url VARCHAR(500),
    gradient_class VARCHAR(60) DEFAULT 'gradient-blue',
    is_featured TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_case_category (category),
    INDEX idx_case_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE gallery_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    image_url VARCHAR(500),
    description TEXT,
    gradient_class VARCHAR(60) DEFAULT 'gradient-blue',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_gallery_category (category),
    INDEX idx_gallery_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE testimonials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    role VARCHAR(120),
    company VARCHAR(120),
    rating INT NOT NULL DEFAULT 5,
    quote TEXT NOT NULL,
    image_url VARCHAR(500),
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_testimonials_active_rating (is_active, rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE contact_inquiries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL,
    phone VARCHAR(40) NOT NULL,
    company VARCHAR(150) NOT NULL,
    country VARCHAR(100) NOT NULL,
    job_title VARCHAR(120) NOT NULL,
    job_details TEXT NOT NULL,
    message TEXT NOT NULL,
    service_interest VARCHAR(150) DEFAULT 'General Inquiry',
    source VARCHAR(50) DEFAULT 'Website',
    status ENUM('New','Contacted','In Progress','Closed') NOT NULL DEFAULT 'New',
    admin_comment TEXT,
    confirmation_email_status VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_inquiries_status (status),
    INDEX idx_inquiries_country (country),
    INDEX idx_inquiries_company (company),
    INDEX idx_inquiries_job_title (job_title),
    INDEX idx_inquiries_date (created_at),
    INDEX idx_inquiries_service (service_interest)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE inquiry_replies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inquiry_id INT NOT NULL,
    admin_id INT,
    subject VARCHAR(200) NOT NULL,
    reply_body TEXT NOT NULL,
    email_status VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reply_inquiry FOREIGN KEY (inquiry_id) REFERENCES contact_inquiries(id) ON DELETE CASCADE,
    CONSTRAINT fk_reply_admin FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_reply_inquiry (inquiry_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE chatbot_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_token VARCHAR(80) NOT NULL,
    user_message TEXT NOT NULL,
    bot_reply TEXT NOT NULL,
    page_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chatbot_visitor (visitor_token),
    INDEX idx_chatbot_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE chatbot_inquiries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_token VARCHAR(80),
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL,
    phone VARCHAR(40),
    company VARCHAR(150),
    service_interest VARCHAR(150),
    message TEXT NOT NULL,
    status ENUM('New','Contacted','In Progress','Closed') NOT NULL DEFAULT 'New',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chatbot_inquiry_date (created_at),
    INDEX idx_chatbot_inquiry_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE event_registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL,
    phone VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event_registration_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    INDEX idx_event_registrations_event (event_id),
    INDEX idx_event_registrations_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO admins (name, email, password_hash) VALUES
('AI-Solutions Admin', 'admin@ai-solutions.com', 'pbkdf2:sha256:1000000$aisolutions2026$888288116b5b769715a3be05cf490cb2c3f7586f8bcdb7c5f7f84fc9da5ad764');

INSERT INTO services (title, slug, short_description, description, icon, industry, display_order, is_active) VALUES
('AI Virtual Assistant', 'ai-virtual-assistant', 'Smart assistants for support, FAQs and customer inquiry collection.', 'Deploy intelligent AI assistants that answer customer questions, automate support tasks, collect inquiry details, guide visitors to pages and provide 24/7 service support for businesses.', '🤖', 'Business', 1, 1),
('AI Prototyping Solutions', 'ai-prototyping-solutions', 'Rapid proof-of-concept development for AI ideas.', 'Transform your AI concept into a working prototype. We help validate feasibility, test user flows and prepare early-stage demonstrations before full-scale development.', '💡', 'Technology', 2, 1),
('Software Engineering Solutions', 'software-engineering-solutions', 'Custom AI-integrated software for business requirements.', 'Build maintainable web applications, dashboards, admin systems and data-driven platforms with clean code, secure authentication and scalable architecture.', '💻', 'Technology', 3, 1),
('Data Analytics Dashboards', 'data-analytics-dashboards', 'Clear dashboards that turn data into useful decisions.', 'Create dashboards with useful charts, reports and filtered views so managers can understand customer inquiries, service interest and business performance.', '📊', 'Finance', 4, 1),
('Healthcare AI Support', 'healthcare-ai-support', 'Patient-support and workflow automation concepts for healthcare teams.', 'Plan AI-supported communication flows, scheduling support and reporting systems with privacy-aware design and human review.', '🩺', 'Healthcare', 5, 1),
('Education Automation Platform', 'education-automation-platform', 'Digital learning and admin workflow support for education providers.', 'Develop student inquiry management, progress reporting and AI-assisted information systems for education businesses.', '🎓', 'Education', 6, 1);

INSERT INTO articles (title, slug, category, author, summary, content, image_url, published_at, is_featured, is_active) VALUES
('The Future of AI in Enterprise: Trends to Watch in 2026', 'future-of-ai-in-enterprise-2026', 'Featured Article', 'Sarah Chen', 'A practical overview of how AI can support enterprise productivity, automation and customer service in 2026.', 'Artificial intelligence is becoming a core part of modern business systems. Companies are using AI assistants, analytics dashboards and automation tools to reduce manual work and improve customer experience. A successful AI project should begin with clear requirements, secure data handling and a user-friendly interface. For small and medium businesses, the best approach is to start with a focused prototype, collect feedback and then improve the system step by step.', '', '2026-05-10', 1, 1),
('Implementing AI Virtual Assistants: A Step-by-Step Guide', 'implementing-ai-virtual-assistants', 'Implementation', 'Michael Rodriguez', 'Learn how to successfully plan and deploy an AI virtual assistant for customer support.', 'A useful virtual assistant starts with a well-defined purpose. First, identify the most common customer questions. Second, design conversation flows and escalation paths. Third, connect the assistant with existing inquiry forms or dashboards. Finally, test the assistant with real users and improve it based on feedback.', '', '2026-05-08', 0, 1),
('AI in Healthcare: Revolutionizing Patient Care', 'ai-in-healthcare-revolutionizing-patient-care', 'Healthcare', 'Dr. Emily Watson', 'Discover how AI can support healthcare teams through diagnostics, scheduling and patient support.', 'Healthcare AI tools can assist with administrative tasks, patient communication, basic triage and data analysis. These systems must be designed carefully with privacy, accuracy and human oversight as key priorities.', '', '2026-05-01', 0, 1),
('Machine Learning Best Practices for 2026', 'machine-learning-best-practices-2026', 'Technology', 'Alex Johnson', 'Best practices for planning, training and deploying machine learning projects.', 'Machine learning projects require clean data, clear objectives and continuous evaluation. Teams should document assumptions, test models properly and design systems that are understandable for non-technical stakeholders.', '', '2026-04-28', 0, 1),
('Ethical Considerations in AI Development', 'ethical-considerations-in-ai-development', 'Ethics', 'Sarah Chen', 'Key ethical principles for responsible AI development and deployment.', 'Responsible AI development should consider fairness, transparency, privacy, security and accountability. These principles help build user trust and reduce risk.', '', '2026-04-20', 0, 1),
('Natural Language Processing in Customer Service', 'nlp-in-customer-service', 'Technology', 'Lisa Thompson', 'How NLP supports customer service through faster responses and improved satisfaction.', 'Natural language processing helps systems understand customer messages, identify intent and route inquiries to the correct team. It can improve response speed when combined with proper human review.', '', '2026-04-15', 0, 1),
('ROI of AI: Measuring Business Impact', 'roi-of-ai-measuring-business-impact', 'Business', 'Robert Kim', 'A simple guide to measuring AI system value through lead response time, cost savings and customer satisfaction.', 'AI return on investment should be measured through practical business indicators such as reduced manual tasks, faster support responses, improved lead tracking and better decision-making from analytics dashboards.', '', '2026-04-10', 0, 1);

INSERT INTO events (title, event_date, event_time, location, short_description, description, image_url, category, is_active) VALUES
('AI Innovation Summit 2026', '2026-06-15', '09:00:00', 'San Francisco, CA', 'Join industry leaders for two days of AI insights and networking.', 'A complete AI summit covering virtual assistants, automation, machine learning and business implementation strategies.', '', 'Conference', 1),
('Healthcare AI Workshop', '2026-07-12', '10:00:00', 'Boston, MA', 'Hands-on workshop exploring AI applications in healthcare.', 'Learn about diagnostic assistance, patient care optimization and ethical data management in healthcare AI solutions.', '', 'Workshop', 1),
('Enterprise AI Webinar Series', '2026-07-20', '14:00:00', 'Online', 'Monthly webinar series for enterprise AI implementation.', 'A practical session for managers and developers planning AI-enabled products and dashboards.', '', 'Webinar', 1),
('Finance AI Automation Conference', '2026-08-05', '08:30:00', 'New York, NY', 'Explore AI applications in fraud detection and risk modelling.', 'Understand how finance teams can use AI for automation, reporting and better decision-making.', '', 'Conference', 1),
('Developer Meetup: Building Flask Dashboards', '2026-06-30', '16:00:00', 'Kathmandu, Nepal', 'A beginner-friendly meetup focused on Flask dashboard development.', 'This meetup demonstrates how to connect Flask, MySQL and a responsive admin panel for real web projects.', '', 'Meetup', 1),
('Past AI Planning Session', '2026-05-15', '11:00:00', 'Online', 'A completed planning session used as an example of past events.', 'This event date has passed, so the website will not show a register button for it.', '', 'Past Event', 1);

INSERT INTO case_studies (title, category, client_name, summary, before_text, after_text, result_metric, image_url, gradient_class, is_featured, is_active) VALUES
('Virtual Assistant for Customer Support', 'AI Virtual Assistant', 'TechCorp', 'Implemented a conversational assistant to answer FAQs and collect lead details before human follow-up.', 'Manual response process with scattered inquiries.', 'Centralised chatbot and admin dashboard with saved inquiries.', '42% faster first response', '', 'gradient-blue', 1, 1),
('Finance Automation Dashboard', 'Data Analytics', 'FinSight Group', 'Designed an analytics dashboard for inquiry tracking, regional reports and service demand analysis.', 'Spreadsheet-based tracking with limited visibility.', 'Live dashboard with filters, charts and export tools.', '3x faster reporting', '', 'gradient-indigo', 1, 1),
('Education Platform Inquiry System', 'Software Engineering', 'EduFlow', 'Built a responsive contact and admin system for managing student and partner inquiries.', 'No structured enquiry workflow.', 'Secure form, status tracking and admin replies.', '65% improved lead organisation', '', 'gradient-green', 1, 1),
('Healthcare AI Prototype', 'Healthcare', 'CareNext', 'Created a proof-of-concept for AI-supported patient communication and triage guidance.', 'Concept only, no interactive demo.', 'Clickable prototype and Flask demo-ready workflow.', 'Prototype approved for next phase', '', 'gradient-purple', 0, 1);

INSERT INTO gallery_items (title, category, image_url, description, gradient_class, is_active) VALUES
('AI Conference 2025', 'Conference', '', 'A memorable event focused on AI product discussions and networking.', 'gradient-blue', 1),
('Team Innovation Workshop', 'Workshop', '', 'Team members collaborating on AI product ideas and wireframes.', 'gradient-purple', 1),
('Healthcare AI Demo', 'Demo', '', 'A demonstration of AI-based healthcare support tools.', 'gradient-green', 1),
('Product Launch Event', 'Launch', '', 'A launch event presenting AI-powered software solutions.', 'gradient-orange', 1),
('Tech Summit Keynote', 'Conference', '', 'Keynote session on responsible AI and automation.', 'gradient-red', 1),
('Client Success Story', 'Client', '', 'A successful client implementation story.', 'gradient-indigo', 1),
('Industry Awards', 'Awards', '', 'Recognition for innovative AI software solutions.', 'gradient-pink', 1),
('Developer Meetup', 'Meetup', '', 'Developers discussing Flask, MySQL and AI features.', 'gradient-teal', 1);

INSERT INTO testimonials (name, role, company, rating, quote, image_url, is_active) VALUES
('John Smith', 'CEO', 'TechCorp', 5, 'Excellent AI service and support for our company. The virtual assistant has transformed our customer service operations.', '', 1),
('Sarah Johnson', 'CTO', 'InnovateLab', 5, 'Their AI prototyping service helped us validate our concept quickly and efficiently. Highly recommended.', '', 1),
('Michael Lee', 'Operations Manager', 'GrowthWorks', 4, 'The team delivered a clean, responsive web solution that made inquiry management much easier.', '', 1),
('Rita Sharma', 'Founder', 'SmartBiz', 5, 'The dashboard and contact system helped us manage leads professionally from one place.', '', 1),
('Anil Pandey', 'Project Client', 'AI Solutions Client', 5, 'The layout is clean, easy to navigate and useful for managing customer requirements.', '', 1),
('Maya Gurung', 'Product Lead', 'NextAI Labs', 4, 'The portfolio, inquiry flow and admin response features make the product feel complete.', '', 1);

INSERT INTO contact_inquiries (name, email, phone, company, country, job_title, job_details, message, service_interest, source, status, confirmation_email_status) VALUES
('Ram Manager', 'ram@example.com', '+977 9800000000', 'XYZ Pvt Ltd', 'Nepal', 'Manager', 'Need a system for customer inquiry management.', 'I am interested in AI virtual assistant and admin dashboard services.', 'AI Virtual Assistant', 'Website', 'New', 'Sample data'),
('John Developer', 'john@example.com', '+1 555 123 4567', 'ABC Tech', 'United States', 'Developer', 'Looking for AI prototype support.', 'Please contact me regarding AI prototyping for a startup idea.', 'AI Prototyping Solutions', 'Website', 'Contacted', 'Sample data'),
('Sita Analyst', 'sita@example.com', '+977 9811111111', 'Data Nepal', 'Nepal', 'Business Analyst', 'We want reports and charts for monthly inquiries.', 'Please suggest an analytics dashboard for our organisation.', 'Data Analytics Dashboards', 'Chatbot', 'In Progress', 'Sample data');

INSERT INTO chatbot_messages (visitor_token, user_message, bot_reply, page_url) VALUES
('sample-visitor', 'What services do you offer?', 'We provide AI virtual assistants, AI prototyping, software engineering, automation dashboards and analytics systems.', '/'),
('sample-visitor', 'I need a quote', 'Pricing depends on scope, timeline and integrations. Please share your company, email and requirement for a detailed quotation.', '/services');

INSERT INTO chatbot_inquiries (visitor_token, name, email, phone, company, service_interest, message, status) VALUES
('sample-visitor', 'Sita Analyst', 'sita@example.com', '+977 9811111111', 'Data Nepal', 'Data Analytics Dashboards', 'We want reports and charts for monthly inquiries.', 'New');

INSERT INTO inquiry_replies (inquiry_id, admin_id, subject, reply_body, email_status) VALUES
(2, 1, 'Reply from AI-Solutions', 'Thank you for your inquiry. We can schedule a short call to discuss your AI prototype requirements.', 'Sample saved reply');
