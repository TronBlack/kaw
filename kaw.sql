/*
 Navicat MySQL Data Transfer

 Source Server         : abe
 Source Server Type    : MySQL
 Source Server Version : 50730
 Source Host           : 127.0.0.1:3306
 Source Schema         : kaw

 Target Server Type    : MySQL
 Target Server Version : 50730
 File Encoding         : 65001

 Date: 18/06/2020 14:05:52
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for assets
-- ----------------------------
DROP TABLE IF EXISTS `assets`;
CREATE TABLE `assets` (
  `asset_id` int(11) NOT NULL AUTO_INCREMENT,
  `vout_id` int(11) NOT NULL DEFAULT '0',
  `asset` varchar(32) COLLATE ascii_bin NOT NULL,
  `amount` double(20,8) NOT NULL DEFAULT '0.00000000',
  `units` int(4) NOT NULL DEFAULT '0',
  `reissuable` int(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`asset_id`) USING BTREE,
  KEY `asset_index` (`asset`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=51810 DEFAULT CHARSET=ascii COLLATE=ascii_bin;

-- ----------------------------
-- Table structure for blocks
-- ----------------------------
DROP TABLE IF EXISTS `blocks`;
CREATE TABLE `blocks` (
  `block_id` int(11) NOT NULL,
  `time` int(11) NOT NULL,
  `block_hash` varchar(64) COLLATE ascii_bin NOT NULL,
  PRIMARY KEY (`block_id`) USING BTREE,
  UNIQUE KEY `Hash` (`block_hash`) USING BTREE COMMENT 'Make sure it is unique so we don''t add a hash twice'
) ENGINE=InnoDB DEFAULT CHARSET=ascii COLLATE=ascii_bin;

-- ----------------------------
-- Table structure for msgs
-- ----------------------------
DROP TABLE IF EXISTS `msgs`;
CREATE TABLE `msgs` (
  `msg_id` int(11) NOT NULL,
  `tx_id` int(11) DEFAULT NULL,
  `asset_id` int(11) DEFAULT NULL,
  `msg_type` int(11) DEFAULT NULL,
  `msg_index` int(255) NOT NULL DEFAULT '0',
  `msg` varchar(64) COLLATE ascii_bin NOT NULL,
  `msg_mime` varchar(255) COLLATE ascii_bin DEFAULT NULL,
  PRIMARY KEY (`msg_id`,`msg`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=ascii COLLATE=ascii_bin;

-- ----------------------------
-- Table structure for txs
-- ----------------------------
DROP TABLE IF EXISTS `txs`;
CREATE TABLE `txs` (
  `tx_id` int(11) NOT NULL AUTO_INCREMENT,
  `block_id` int(11) NOT NULL,
  `tx_hash` varchar(64) COLLATE ascii_bin NOT NULL,
  PRIMARY KEY (`tx_id`) USING BTREE,
  UNIQUE KEY `tx_hash_index` (`tx_hash`) USING BTREE COMMENT 'Tx hash should only be in db once'
) ENGINE=InnoDB AUTO_INCREMENT=108972 DEFAULT CHARSET=ascii COLLATE=ascii_bin;

-- ----------------------------
-- Table structure for vouts
-- ----------------------------
DROP TABLE IF EXISTS `vouts`;
CREATE TABLE `vouts` (
  `vout_id` int(11) NOT NULL AUTO_INCREMENT,
  `tx_id` int(11) NOT NULL,
  `vnum` int(11) NOT NULL DEFAULT '0',
  `address` varchar(40) COLLATE ascii_bin NOT NULL,
  `asset_id` int(11) NOT NULL DEFAULT '0' COMMENT 'If asset_id is 0 then referencing RVN',
  `sats` bigint(48) NOT NULL DEFAULT '0',
  `spent` int(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`vout_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1353583 DEFAULT CHARSET=ascii COLLATE=ascii_bin;

SET FOREIGN_KEY_CHECKS = 1;
