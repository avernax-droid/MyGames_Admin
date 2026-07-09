-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: mygames_dev
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `canais_aquisicao`
--

LOCK TABLES `canais_aquisicao` WRITE;
/*!40000 ALTER TABLE `canais_aquisicao` DISABLE KEYS */;
INSERT INTO `canais_aquisicao` VALUES (1,'google','🔍 Google',1),(2,'mercado_livre','🤝 Mercado Livre',1),(3,'youtube','▶️ YouTube',1),(4,'indicacao_amigo','🗣️ Indicação de Amigo',1),(5,'redes_sociais','📱 Redes Sociais',1),(6,'outros','✨ Outros',1);
/*!40000 ALTER TABLE `canais_aquisicao` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `catalogo_mestre`
--

LOCK TABLES `catalogo_mestre` WRITE;
/*!40000 ALTER TABLE `catalogo_mestre` DISABLE KEYS */;
INSERT INTO `catalogo_mestre` VALUES (1,'Controle Xbox One',2,'Microsoft',329.99,120.00,150.00,NULL,'f0177658-7f2c-4a81-88fa-947f8c7b9328',1),(2,'Jogos PlayStation 3',4,'Sony',49.99,5.00,5.00,NULL,'c9a4ba93-16c2-4276-900b-a90ae87c0c54',1),(3,'Playstation 4 Fat - 500GB',1,'Sony',1399.99,900.00,950.00,NULL,'f1574a67-d4c7-4d29-a71e-c3976036ff69',1),(4,'Xbox One S - All Digital',1,'Microsoft',1499.00,950.00,1000.00,NULL,'f0219be9-5701-4479-859d-0cb18fb5372d',1),(5,'Controle Navigator',2,'Sony',149.99,30.00,40.00,NULL,'5a88870c-b46f-4f9e-9f28-30449f14d2f4',1),(6,'PlayStation 1',1,'Sony',599.99,300.00,350.00,NULL,'57438f69-f86a-44b1-98fc-a76f3ff7d31b',1),(7,'PlayStation 2 FAT',1,'Sony',899.99,450.00,500.00,NULL,'22cf8461-39fb-4560-8c5e-407ff1c8224d',1),(8,'PlayStation 2 Slim',1,'Sony',699.99,300.00,350.00,NULL,'4d455b20-af99-4d38-8131-da6f1106e7d9',1),(9,'Controle PS1 | PS2',2,'Sony',69.99,25.00,30.00,NULL,'6ee320f8-0594-4658-9122-4c91b1830d88',1),(10,'PlayStation Vita (Old)',1,'Sony',1499.99,900.00,950.00,NULL,'969a6f06-09f3-4a52-b45f-ce57faaf6e60',1),(11,'PlayStation Vita (New)',1,'Sony',1599.99,1000.00,1050.00,NULL,'20f395e0-67cf-49c5-85a6-6345394d5d31',1),(12,'PlayStation Portable - PSP',1,'Sony',799.99,450.00,500.00,NULL,'4c19f427-0364-409e-a66a-d02f45058414',1),(13,'Playstation 3 Slim e Super - 120 GB',1,'Sony',899.99,500.00,550.00,NULL,'f9958180-0260-4c9e-b163-1d2494518b60',1),(14,'Playstation 3 Slim e Super - 160 GB',1,'Sony',949.99,550.00,600.00,NULL,'475ea328-de36-4d81-8b0a-acaaf03a0362',1),(15,'Playstation 3 Slim e Super - 250 GB',1,'Sony',999.99,600.00,650.00,NULL,'c826e99d-93ec-4f13-95af-5689712d2459',1),(16,'Playstation 3 Slim e Super - 500 GB',1,'Sony',999.99,650.00,700.00,NULL,'9adf1c9e-58aa-4248-8fb6-e8ce1132c91b',1),(17,'Jogos Esporte',4,'Sony',0.00,5.00,5.00,NULL,'91357bda-f27f-4c62-9348-6addb092e571',0),(18,'Controle PlayStation 3',2,'Sony',179.99,40.00,50.00,NULL,'0bc4ed95-effe-42f6-a2a1-00a4769c8308',1),(19,'Camera PlayStation 3',3,'Sony',59.99,10.00,20.00,NULL,'f728781f-8b2a-4759-83a3-0bd0bb8d3e16',1),(20,'Controle Move',2,'Sony',149.99,20.00,30.00,NULL,'66a6f8a4-62f3-4db4-b237-8dc807604b48',1),(21,'Playstation 4 Fat - 1TB',1,'Sony',1499.99,1000.00,1050.00,NULL,'46c0b649-122c-4951-b97c-a57e9964eab1',1),(22,'Playstation 4 Slim - 500GB',1,'Sony',1599.99,1050.00,1100.00,NULL,'93a793a7-cc2b-4881-8c1a-3747b8494cb0',1),(23,'Playstation 4 Slim - 1TB',1,'Sony',1699.99,1150.00,1200.00,NULL,'9789f38b-0d43-417a-a294-952fa56574e0',1),(24,'Playstation 4 Pro - 1TB',1,'Sony',2299.99,1400.00,1500.00,NULL,'0b35d7c0-f019-4d99-9ead-360db072d7b4',1),(25,'Playstation 4 Pro - Personalizado',1,'Sony',2399.99,1500.00,1600.00,NULL,'5718fad2-fd5c-4aa0-a5b9-739da79ccf33',1),(26,'Jogos PlayStation 4',4,'Sony',79.99,20.00,20.00,NULL,'9484bd63-fe3a-41b2-8672-50d1568e113b',1),(27,'Controle PlayStation 4',2,'Sony',229.99,70.00,80.00,NULL,'d9253ff6-82c3-45fd-8be7-95bffd4bb4f6',1),(28,'VR1 Óculos PlayStation 4',3,'Sony',1599.99,900.00,950.00,NULL,'3244a57d-3fba-4642-bd68-ab5f1e007fdd',1),(29,'Camera PlayStation 4',3,'Sony',199.99,40.00,50.00,NULL,'feb55b82-5a26-46fc-95b9-dc86f03407b1',1),(30,'PlayStation 5 Fat com Disco',1,'Sony',3599.99,2300.00,2400.00,NULL,'fb0f776c-d4ed-4328-bacb-4636251fcff7',1),(31,'PlayStation 5 Fat Digital',1,'Sony',3399.99,2100.00,2200.00,NULL,'e21cc6ae-9bc9-4ee5-af75-ffb3bc4b1344',1),(32,'PlayStation 5 Slim - Disco',1,'Sony',3799.99,2600.00,2700.00,NULL,'16af46cb-db66-442e-81e8-a19afa54223a',1),(33,'PlayStation 5 Slim - Digital',1,'Sony',3599.99,2400.00,2500.00,NULL,'e5db2c68-0e14-4692-b93f-b48dd51e87af',1),(34,'Controle PlayStation 5',2,'Sony',349.99,150.00,180.00,NULL,'a9a9b3ff-f91b-47e9-a723-432d521be2bc',1),(35,'Jogos PlayStation 5',4,'Sony',299.99,100.00,130.00,NULL,'cb65c2c4-a5a7-4aaa-b6de-3a588583a70c',1),(36,'Volantes PlayStation 5',3,'Sony',1599.99,800.00,900.00,NULL,'8876f008-a3aa-45c7-974e-edbf991b77ec',1),(37,'Xbox 1',1,'Microsoft',999.99,400.00,500.00,NULL,'1da36cf1-8444-44f0-bbb0-94b07f879e99',1),(38,'Jogos Xbox 1 Clássico',4,'Microsoft',79.99,20.00,25.00,NULL,'d5543a9f-41e6-4578-866f-dcae2f7ae23a',1),(39,'Controle Xbox 1 Clássico',2,'Microsoft',149.99,50.00,60.00,NULL,'8d26d820-5b3b-4950-bc46-050c1bae3361',1),(40,'Xbox 360 - 4GB',1,'Microsoft',599.99,400.00,450.00,NULL,'4a2cca1e-2cf0-4c54-8d02-fb6729cb5a00',1),(41,'Xbox 360 - 250GB',1,'Microsoft',649.99,450.00,500.00,NULL,'4ae5440c-9c2e-4679-b509-705522650169',1),(42,'Xbox 360 - 500GB',1,'Microsoft',699.99,500.00,550.00,NULL,'d9b67f4c-36cf-4b06-b97e-5282c1a74ec8',1),(43,'Kinect Xbox 360',3,'Microsoft',79.99,15.00,20.00,NULL,'0d73ba68-f086-4001-b106-b10e698f58e4',1),(44,'Xbox One Fat - 500GB',1,'Microsoft',1199.99,800.00,850.00,NULL,'cdf79e14-4b00-4bdf-809d-9997c7372eca',1),(45,'Xbox One Fat - 1TB',1,'Microsoft',1299.99,850.00,900.00,NULL,'d093a2cd-6ab4-4c2c-b34f-6ee6f56d7167',1),(46,'Xbox One X - 1TB',1,'Microsoft',1999.99,1200.00,1300.00,NULL,'e9a7b7a3-fe62-4393-8153-62b6bc5fcc94',1),(47,'Jogos Xbox One',4,'Microsoft',79.99,15.00,15.00,NULL,'7e26632b-e80e-47ff-b4ea-8f7e5136bbcc',1),(48,'Kinect Xbox One',3,'Microsoft',149.99,35.00,40.00,NULL,'84e17d15-bdce-4306-8916-d6c571613b8a',1),(49,'Controle Xbox Series',2,'Microsoft',349.99,100.00,150.00,NULL,'f1e4f7b4-3ffc-425d-91bb-5486bb5e7f60',1),(50,'Câmbio Xbox G29/G920',3,'Microsoft',299.99,120.00,150.00,NULL,'6e50bc58-c0a3-4d3b-ac74-4241756798e0',1),(51,'Super Nintendo',1,'Nintendo',599.99,350.00,400.00,NULL,'05d70d19-d84e-4e62-89e5-1430dd1e9248',1),(52,'Jogos Super Nintendo',4,'Nintendo',0.00,0.00,0.00,NULL,'e7ad771d-7f00-447e-a9b2-37e9fd1147ac',0),(53,'Controle Super Nintendo',2,'Nintendo',79.99,30.00,40.00,NULL,'17f63175-c30a-4235-9b2f-b07979d181c8',1),(54,'Nintendo 64',1,'Nintendo',599.99,350.00,400.00,NULL,'73d49bbe-0d63-4110-875e-1c5f3f68f5b9',1),(55,'Controle N64',2,'Nintendo',149.99,50.00,60.00,NULL,'fa9cd06e-1b35-463a-8f3f-71ccc459fea8',1),(56,'Super Nintendo - Baby',1,'Nintendo',399.99,150.00,170.00,NULL,'31d77ba3-239d-4221-a864-b3f150b057db',1),(57,'Nintendo DS Lite',1,'Nintendo',399.99,200.00,250.00,NULL,'c0f91cf7-dfe4-4ff3-9ae3-4b8bbaba1ba7',1),(58,'Nintendo DS XL',1,'Nintendo',499.99,250.00,300.00,NULL,'1934abf4-1b51-49ed-beb4-8aa56320c623',1),(59,'Nintendo 2DS',1,'Nintendo',599.99,400.00,450.00,NULL,'ba46bdd3-459c-47e6-85c8-41ffc587bd02',1),(60,'Nintendo New 2DS XL',1,'Nintendo',1299.99,700.00,750.00,NULL,'3b3ee2a0-4a59-4ac4-929d-a7866b954856',1),(61,'Nintendo 3DS',1,'Nintendo',799.99,500.00,550.00,NULL,'e5ad5cbb-8282-4d9e-a3cd-81a450baed96',1),(62,'Nintendo 3DS XL',1,'Nintendo',1599.99,850.00,900.00,NULL,'441decda-6080-4d86-9ada-9fa11afab5a7',1),(63,'Nintendo New 3DS XL',1,'Nintendo',1999.99,1200.00,1250.00,NULL,'800847e4-2da9-4acb-9c2b-1ebf1f306ee2',1),(64,'Jogos 3DS',4,'Nintendo',99.99,5.00,15.00,NULL,'982d9f7e-98cd-4d12-b5c1-fc9cbd21922f',1),(65,'Wii',1,'Nintendo',699.99,350.00,400.00,NULL,'bbe21b8b-387a-4326-846b-caa02359599f',1),(66,'Jogos Wii',4,'Nintendo',79.99,5.00,10.00,NULL,'95f05d3c-dd13-4c78-844c-d71487ed5bf0',1),(67,'Controle Wii (O par)',2,'Nintendo',249.99,45.00,50.00,NULL,'dc419737-acdb-4fd4-a65a-ab9f7bac107a',1),(68,'WiiU',1,'Nintendo',1599.99,950.00,1000.00,NULL,'986576d6-2fd5-4fff-b49e-f87372e6e6c7',1),(69,'Jogos WiiU',4,'Nintendo',79.99,10.00,15.00,NULL,'be3644f2-1628-453e-8f8e-d7048434aeb8',1),(70,'Controle WiiU',2,'Nintendo',199.99,50.00,60.00,NULL,'f83f99a8-8074-41a4-aef3-54ecb4baca25',1),(71,'Jogos Xbox 360',4,'Microsoft',79.99,10.00,15.00,NULL,'6a640fb1-2445-4004-b8a2-e2c9f329502b',1),(72,'Jogos Top',4,'Sony',0.00,20.00,20.00,NULL,'02eb07a6-8631-4673-82d8-46cdcd2c40b3',0),(73,'PlayStation 5 Pro',1,'Sony',5599.99,3700.00,3800.00,NULL,'f6cde0ee-bc7b-4608-b8aa-c5d7e1431ad9',1),(74,'Controle Xbox 360',2,'Microsoft',179.99,50.00,60.00,NULL,'3195b32d-27e0-4658-a0af-e4a87e7b50a0',1),(75,'Xbox Series X - 1TB',1,'Microsoft',4799.99,3300.00,3400.00,NULL,'396d9bf2-3349-4b6e-bb01-13037ea60e1d',1),(76,'Jogos N64',4,'Nintendo',0.00,0.00,0.00,NULL,'1f389457-25cb-4a1b-ba04-a6bbf96193aa',0),(77,'Xbox Series S - 512GB',1,'Microsoft',2399.99,1800.00,1850.00,NULL,'250e0213-deaa-4cf8-afc0-707046a6380b',1),(78,'Jogos DS',4,'Nintendo',0.00,5.00,5.00,NULL,'c81de10a-1756-4fb2-8f23-5bd7da171ddd',0),(79,'Nintendo Switch',1,'Nintendo',1699.00,1000.00,1050.00,NULL,'a1c177c0-80d4-4c23-9af4-48c1342eeb7c',1),(80,'Camera PlayStation 5',3,'Sony',299.00,150.00,170.00,NULL,'05363631-6568-434e-badd-b735d3bc1139',1),(81,'Xbox One S - 500GB',1,'Microsoft',1499.99,900.00,950.00,NULL,'13dbdb8e-b703-4f37-bd09-42dc7276fb5d',1),(82,'Volante Xbox G29/G920',3,'Microsoft',1499.99,800.00,850.00,NULL,'dce2ee82-e009-4754-8112-fa3653001c62',1),(83,'Volantes PlayStation 4',3,'Sony',1599.99,850.00,900.00,NULL,'182e1445-23b6-4f6f-b684-838d225c0db0',1),(84,'VR2 Óculos PlayStation 5',3,'Sony',1799.99,1200.00,1300.00,NULL,'d571a9dd-5952-4f87-aa3d-4ad0b2f25129',1),(85,'PS Portal',3,'Sony',1399.00,900.00,950.00,NULL,'e4c6ea1d-fffd-498a-8599-9e0a2918ad33',1),(86,'Nintendo Switch Oled',1,'Nintendo',1999.99,1400.00,1450.00,NULL,'9697bf2a-9e9e-46d2-a3eb-996ff1339f91',1),(87,'Jogos Nintendo Switch',4,'Nintendo',249.90,100.00,130.00,NULL,'b02e74c1-a34d-4833-9070-046ab6df9f41',1),(88,'Jogos Ruins',4,'Nintendo',149.99,20.00,50.00,NULL,'5fa4aa6b-8123-4b6e-98c2-42910c5e9305',1),(89,'Controle Nintendo Switch',2,'Nintendo',299.99,130.00,150.00,NULL,'1127d82c-f1fc-4763-ac0c-d5605b4362b3',1),(90,'Xbox One S - 1TB',1,'Microsoft',1599.99,950.00,1000.00,NULL,'a4b77fdb-ca0c-464b-a0dd-0923d15e55f2',1),(91,'Nintendo Switch 2',1,'Nintendo',3499.99,2200.00,2300.00,NULL,'101ffe61-15c1-4324-8b2e-8258344e4c1c',1),(92,'Nintendo Switch Lite',1,'Nintendo',1099.99,750.00,800.00,NULL,'e367ee12-f210-434f-8bc2-7bf5bc9af981',1);
/*!40000 ALTER TABLE `catalogo_mestre` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `categorias`
--

LOCK TABLES `categorias` WRITE;
/*!40000 ALTER TABLE `categorias` DISABLE KEYS */;
INSERT INTO `categorias` VALUES (1,'Console',1),(2,'Controle',1),(3,'Acessório',1),(4,'Jogo',1);
/*!40000 ALTER TABLE `categorias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `categorias_avaliacao`
--

LOCK TABLES `categorias_avaliacao` WRITE;
/*!40000 ALTER TABLE `categorias_avaliacao` DISABLE KEYS */;
INSERT INTO `categorias_avaliacao` VALUES (1,'Estado do Aparelho','estado-aparelho',1,1),(2,'Acessórios Inclusos','itens-inclusos',1,1),(3,'Estado da Mídia','estado-midia',4,1),(4,'Estado da Embalagem','estado-embalagem',NULL,0);
/*!40000 ALTER TABLE `categorias_avaliacao` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `dados_empresa`
--

LOCK TABLES `dados_empresa` WRITE;
/*!40000 ALTER TABLE `dados_empresa` DISABLE KEYS */;
INSERT INTO `dados_empresa` VALUES (1,'ROCK LASER INTERNACIONAL COM','Rock Laser','29322164000117','07042040','Rua Engenheiro Camilo Olivetti','295','loja c 14','Itapegica-Vila Hermínia','Guarulhos','SP','11993820330','rocklaser@uol.com.br');
/*!40000 ALTER TABLE `dados_empresa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `opcoes_estado`
--

LOCK TABLES `opcoes_estado` WRITE;
/*!40000 ALTER TABLE `opcoes_estado` DISABLE KEYS */;
INSERT INTO `opcoes_estado` VALUES (20,4,'Produto funcionando em sua embalagem original',NULL,0.00,0),(21,4,'Produto funcionando sem capa ou com capa paralela, de papelão, etc.',NULL,0.00,0),(22,4,'Produto novo, lacrado',NULL,0.00,0),(23,4,'Produto não funciona',NULL,0.00,0),(24,4,'Outro, especifique nos comentários',NULL,0.00,0),(25,3,'Produto funcionando, completo com caixa',NULL,0.00,0),(26,3,'Produto funcionando, completo sem caixa',NULL,0.00,0),(27,3,'Produto funcionando com itens faltantes, especifique nos comentários',NULL,0.00,0),(28,3,'Produto com problemas, especifique nos comentários',NULL,0.00,0),(29,3,'Outro, especifique nos comentários',NULL,0.00,0),(37,1,'Produto não funciona',1.00,0.00,1),(38,1,'Console funcionando, completo com caixa',1.00,0.00,2),(39,1,'Console funcionando, completo sem caixa',1.00,0.00,3),(40,1,'Console funcionando com itens faltantes, especifique nos comentários',1.00,0.00,4),(41,1,'Console completo com problemas, especifique nos comentários',1.00,0.00,5),(42,1,'Console com itens faltantes e com problemas, especifique nos comentários',1.00,0.00,6),(43,1,'Outro, especifique nos comentários',1.00,0.00,7),(44,2,'Produto funcionando, completo com caixa',1.00,0.00,1),(45,2,'Produto funcionando, completo sem caixa',1.00,0.00,2),(46,2,'Produto com problemas, especifique nos comentários',1.00,0.00,3),(47,2,'Outro, especifique nos comentários',1.00,0.00,4);
/*!40000 ALTER TABLE `opcoes_estado` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `perguntas_conservacao`
--

LOCK TABLES `perguntas_conservacao` WRITE;
/*!40000 ALTER TABLE `perguntas_conservacao` DISABLE KEYS */;
INSERT INTO `perguntas_conservacao` VALUES (1,1,'Produto é original e bloqueado?','Sim/Nao',0.00),(2,2,'O Controle é original?','Sim/Nao',0.00),(3,3,'O Acessório é original?','Sim/Nao',0.00),(4,4,'Os jogos são mídia física (CD) ou digital (na Net)?','Sim/Nao',0.00);
/*!40000 ALTER TABLE `perguntas_conservacao` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `regioes_atendimento`
--

LOCK TABLES `regioes_atendimento` WRITE;
/*!40000 ALTER TABLE `regioes_atendimento` DISABLE KEYS */;
INSERT INTO `regioes_atendimento` VALUES (1,'Guarulhos','SP',1.50,1),(2,'São Paulo','SP',1.00,1),(3,'Campinas','SP',0.95,1),(4,'Rio de Janeiro','RJ',1.05,1),(5,'Belo Horizonte','MG',1.00,1),(6,'Curitiba','PR',0.98,1),(7,'Mococa','SP',1.00,1),(8,'Salesópolis','SP',1.00,1),(9,'Paraty','RJ',0.01,1);
/*!40000 ALTER TABLE `regioes_atendimento` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `status_protocolos`
--

LOCK TABLES `status_protocolos` WRITE;
/*!40000 ALTER TABLE `status_protocolos` DISABLE KEYS */;
INSERT INTO `status_protocolos` VALUES (1,'aguardando_o_cliente_levar_o_produto_no_correio','Aguardando o cliente levar o produto no correio','info',1),(2,'produto_recebido','Produto recebido','primary',1),(3,'aguardando_laudo_tecnico','Aguardando laudo técnico','warning',1),(4,'aprovado','Aprovado','success',1),(5,'parcialmente_aprovado','Parcialmente aprovado','dark',1),(6,'negado','Negado','danger',1),(7,'aguardando_pagamento','Aguardando pagamento','info',1),(8,'pagamento_efetuado','Pagamento efetuado com sucesso','success',1),(9,'protocolo_encerrado','Protocolo encerrado','secondary',1),(10,'validar','Validar','#00e676',0),(11,'avaliar','avaliar','#00e676',0),(13,'laudo','Laudo','#00e676',0),(14,'pericia','pericia','#005c51',1);
/*!40000 ALTER TABLE `status_protocolos` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-09 16:25:54
