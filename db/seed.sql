USE khetiyan;

SET NAMES utf8mb4;

INSERT INTO state (id, code, name_hi, name_en) VALUES
  (1, 'RJ', 'राजस्थान', 'Rajasthan');

INSERT INTO district (id, state_id, code, name_hi, name_en) VALUES
  (1, 1, 'JP', 'जयपुर', 'Jaipur'),
  (2, 1, 'AL', 'अलवर', 'Alwar');

INSERT INTO tehsil (id, district_id, code, name_hi, name_en) VALUES
  (1, 1, 'SNG', 'सांगानेर', 'Sanganer'),
  (2, 1, 'AMB', 'आमेर', 'Amber'),
  (3, 2, 'BHR', 'बहरोड़', 'Behror');

INSERT INTO village (id, tehsil_id, code, name_hi, name_en, total_area_hectare) VALUES
  (1, 1, '001', 'भोजपुरा', 'Bhojpura', 412.5000),
  (2, 2, '002', 'निंदर', 'Nindar', 289.7500),
  (3, 3, '003', 'तातारपुर', 'Tatarpur', 176.2500);

INSERT INTO land_type (id, code, name_hi, name_en) VALUES
  (1, 'irrigated',   'सिंचित',   'Irrigated'),
  (2, 'unirrigated', 'असिंचित',  'Unirrigated'),
  (3, 'barren',      'बंजर',     'Barren'),
  (4, 'grazing',     'चारागाह',  'Grazing'),
  (5, 'orchard',     'बाग़',     'Orchard');

INSERT INTO person (id, aadhaar_hash, aadhaar_last4, name_hi, name_en, father_name_hi, gender, date_of_birth, mobile, address_hi) VALUES
  (1, SHA2('100000000001', 256), '0001', 'रामलाल शर्मा',  'Ram Lal Sharma',  'मोहनलाल शर्मा', 'male',   '1961-04-12', '9876500001', 'भोजपुरा, सांगानेर, जयपुर'),
  (2, SHA2('100000000002', 256), '0002', 'सीता देवी',     'Sita Devi',       'श्यामलाल शर्मा', 'female', '1966-09-03', '9876500002', 'भोजपुरा, सांगानेर, जयपुर'),
  (3, SHA2('100000000003', 256), '0003', 'किशन सिंह',     'Kishan Singh',    'हरलाल सिंह',    'male',   '1955-01-25', '9876500003', 'भोजपुरा, सांगानेर, जयपुर'),
  (4, SHA2('100000000004', 256), '0004', 'गीता देवी',     'Geeta Devi',      'रामेश्वर लाल',  'female', '1972-07-18', '9876500004', 'निंदर, आमेर, जयपुर'),
  (5, SHA2('100000000005', 256), '0005', 'अब्दुल रहमान',  'Abdul Rahman',    'करीम ख़ान',     'male',   '1979-11-30', '9876500005', 'निंदर, आमेर, जयपुर'),
  (6, SHA2('100000000006', 256), '0006', 'सुनीता मीणा',   'Sunita Meena',    'भंवर लाल मीणा', 'female', '1985-02-14', '9876500006', 'तातारपुर, बहरोड़, अलवर');

INSERT INTO khasra (id, village_id, khasra_no, area_hectare, land_type_id, soil_type, irrigation_source, boundary, is_disputed) VALUES
  (1, 1, '101/2', 2.5000, 1, 'दोमट',    'नहर',        '[[75.7800,26.8200],[75.7820,26.8200],[75.7820,26.8230],[75.7800,26.8230],[75.7800,26.8200]]', FALSE),
  (2, 1, '102',   1.2500, 2, 'रेतीली',  'कुआँ',       '[[75.7840,26.8240],[75.7860,26.8240],[75.7860,26.8260],[75.7840,26.8260],[75.7840,26.8240]]', FALSE),
  (3, 1, '103/1', 0.8000, 3, 'पथरीली',  NULL,          NULL, FALSE),
  (4, 2, '45',    3.0000, 1, 'दोमट',    'ट्यूबवेल',   '[[75.8100,26.9050],[75.8130,26.9050],[75.8130,26.9080],[75.8100,26.9080],[75.8100,26.9050]]', FALSE),
  (5, 2, '46/3',  1.5000, 1, 'दोमट',    'ट्यूबवेल',   NULL, FALSE),
  (6, 3, '7',     2.0000, 2, 'रेतीली',  'कुआँ',       NULL, TRUE),
  (7, 3, '8',     4.0000, 4, 'रेतीली',  NULL,          NULL, FALSE);

INSERT INTO khata (id, village_id, khata_no, khata_type) VALUES
  (1, 1, '12', 'individual'),
  (2, 1, '13', 'joint'),
  (3, 2, '5',  'individual'),
  (4, 3, '21', 'joint');

INSERT INTO mutation (id, mutation_no, khasra_id, from_person_id, to_person_id, share_percentage, mutation_type, order_date, status, remarks_hi) VALUES
  (1, 'MUT-2024-0001', 5, 4, 5, 100.00, 'sale',        '2024-06-10', 'approved', 'पंजीकृत विक्रय विलेख संख्या 221/2024'),
  (2, 'MUT-2025-0002', 4, 4, 5,  25.00, 'inheritance', '2025-01-15', 'pending',  'विरासत हेतु आवेदन'),
  (3, 'MUT-2025-0003', 3, 3, 2,  50.00, 'correction',  '2025-03-02', 'pending',  'नाम संशोधन हेतु');

INSERT INTO ownership (khasra_id, khata_id, person_id, share_percentage, acquisition_mode, from_date, to_date, source_mutation_id) VALUES
  (1, 2, 1, 60.00, 'inheritance', '2001-07-01', NULL, NULL),
  (1, 2, 2, 40.00, 'inheritance', '2001-07-01', NULL, NULL),
  (2, 1, 1, 100.00, 'inheritance', '2001-07-01', NULL, NULL),
  (3, 1, 3, 100.00, 'sale',        '2010-02-11', NULL, NULL),
  (4, 3, 4, 50.00, 'inheritance', '2005-05-20', NULL, NULL),
  (4, 3, 5, 50.00, 'inheritance', '2005-05-20', NULL, NULL),
  (5, 3, 5, 100.00, 'sale',        '2024-06-10', NULL, 1),
  (6, 4, 6, 100.00, 'government_allotment', '2015-08-09', NULL, NULL);

INSERT INTO crop (id, code, name_hi, name_en) VALUES
  (1,  'wheat',      'गेहूं',      'Wheat'),
  (2,  'bajra',      'बाजरा',      'Pearl Millet'),
  (3,  'mustard',    'सरसों',      'Mustard'),
  (4,  'chana',      'चना',        'Chickpea'),
  (5,  'maize',      'मक्का',      'Maize'),
  (6,  'cotton',     'कपास',       'Cotton'),
  (7,  'groundnut',  'मूंगफली',    'Groundnut'),
  (8,  'moong',      'मूंग',       'Green Gram'),
  (9,  'potato',     'आलू',        'Potato'),
  (10, 'onion',      'प्याज',      'Onion');

INSERT INTO crop_cycle (khasra_id, crop_id, season, crop_year, sown_date, harvested_date, area_hectare, yield_quintal) VALUES
  (1, 1, 'rabi',   2025, '2025-11-05', '2026-03-20', 2.5000, 85.00),
  (1, 2, 'kharif', 2025, '2025-06-25', '2025-10-05', 2.5000, 32.50),
  (2, 3, 'rabi',   2025, '2025-10-28', '2026-02-25', 1.2500, 18.00),
  (4, 6, 'kharif', 2025, '2025-05-30', '2025-11-12', 3.0000, 55.00),
  (4, 1, 'rabi',   2025, '2025-11-10', '2026-03-25', 3.0000, 110.00),
  (5, 7, 'kharif', 2025, '2025-06-15', '2025-10-20', 1.5000, 40.00),
  (6, 5, 'kharif', 2025, '2025-07-01', '2025-10-15', 2.0000, 28.00);

INSERT INTO app_user (id, username, password_hash, full_name_hi, role, village_id, is_active) VALUES
  (1, 'admin',   '$2b$12$b4wP4nMppgCyRIeguTFmHOY2G0u0gw0wYxA.N2kwqYwcHYojvtxS6', 'प्रशासक',        'admin',    NULL, TRUE),
  (2, 'patwari', '$2b$12$2mr3LgwDkLxnuzAl8AKMMuBIdK15gJFZ33Y9kaAoQ5J6QjwvDwZFq', 'रामनिवास जाट', 'patwari', 1,    TRUE);

INSERT INTO land_document (khasra_id, doc_type, file_name, file_uri, uploaded_by) VALUES
  (1, 'khasra_map',    'khasra_101_2_map.pdf',  '/uploads/2024/khasra_101_2_map.pdf',  2),
  (1, 'jamabandi',     'jamabandi_2024.pdf',    '/uploads/2024/jamabandi_2024.pdf',    2),
  (5, 'sale_deed',     'sale_deed_221_2024.pdf','/uploads/2024/sale_deed_221_2024.pdf', 1),
  (4, 'mutation_order','mutation_mut_2025_0002.pdf', '/uploads/2025/mutation_mut_2025_0002.pdf', 1);
