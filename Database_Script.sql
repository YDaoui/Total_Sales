Vérifie si la base existe, sinon la crée
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'Total_Stat')
BEGIN
    CREATE DATABASE Total_Stat;
END
GO

-- Utilisation de la base
USE Total_Stat;
GO

-- Suppression des tables si elles existent (dans l'ordre des dépendances)
IF OBJECT_ID('dbo.Recolt', 'U') IS NOT NULL DROP TABLE dbo.Recolt;
IF OBJECT_ID('dbo.Sales', 'U') IS NOT NULL DROP TABLE dbo.Sales;
IF OBJECT_ID('dbo.Effectifs', 'U') IS NOT NULL DROP TABLE dbo.Effectifs;
IF OBJECT_ID('dbo.Logs', 'U') IS NOT NULL DROP TABLE dbo.Logs;
IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL DROP TABLE dbo.Users;
GO

-- Table Users
CREATE TABLE Users (
    Hyp VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8 PRIMARY KEY,
    UserName NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 UNIQUE NOT NULL,
    PassWord NVARCHAR(255) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    Cnx DATETIME,
    ID_User INT IDENTITY(1,1)
);

-- Table Effectifs
CREATE TABLE Effectifs (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Hyp VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    ID_AGTSDA VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    UserName NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    NOM NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    PRENOM NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    Team NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Type NVARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8 CHECK (Type IN ('Agent', 'Manager', 'Admin')),
    Activité NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Date_In DATE,
    FOREIGN KEY (UserName) REFERENCES Users(UserName)
);

-- Table Sales
CREATE TABLE Sales (
    Hyp VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8 PRIMARY KEY,
    ORDER_REFERENCE VARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 UNIQUE NOT NULL,
    ORDER_DATE DATETIME NOT NULL,
    SHORT_MESSAGE NVARCHAR(255) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Country NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    City NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Total DECIMAL(18,2) CHECK (Total >= 0),
    Rating DECIMAL(3,1) CHECK (Rating BETWEEN 0 AND 5)
);

-- Table Recolt
CREATE TABLE Recolt (
    Hyp VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8 PRIMARY KEY,
    POINT_OF_SELL_LABEL NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    TRANSACTION_AMOUNT DECIMAL(18,2) CHECK (TRANSACTION_AMOUNT >= 0),
    ORDER_REFERENCE VARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    ORDER_DATE DATETIME NOT NULL,
    SHORT_MESSAGE NVARCHAR(255) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    City NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Country NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    FOREIGN KEY (ORDER_REFERENCE) REFERENCES Sales(ORDER_REFERENCE)
);

-- Table Logs
CREATE TABLE Logs (
    Hyp VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8 PRIMARY KEY,
    Groupe NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Origine NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [Num. activité] VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [Num. BP] VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [Sous motif] NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Canal NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Direction NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [Date de création] DATE NOT NULL,
    Qualification NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [Heure création] TIME,
    Offre NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [Date ancienneté client] DATE,
    Segment NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [Statut BP] NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [mode de facturation] NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    [ancienneté client] INT
);

-- Index
CREATE INDEX IX_Users_UserName ON Users(UserName);
CREATE INDEX IX_Effectifs_UserName ON Effectifs(UserName);
CREATE INDEX IX_Effectifs_Team ON Effectifs(Team);
CREATE INDEX IX_Sales_ORDER_DATE ON Sales(ORDER_DATE);
CREATE INDEX IX_Sales_Country ON Sales(Country);
CREATE INDEX IX_Recolt_ORDER_DATE ON Recolt(ORDER_DATE);
CREATE INDEX IX_Logs_DateCreation ON Logs([Date de création]);




-- Supprimer si existe
IF OBJECT_ID('dbo.Effectifs', 'U') IS NOT NULL
    DROP TABLE dbo.Effectifs;
GO

-- Création de la table Effectifs
CREATE TABLE Effectifs (
    ID_effectif INT IDENTITY(1,1), -- Clé technique
    Hyp VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    ID VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    ID_AGTSDA VARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    UserName NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    NOM NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    PRENOM NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8 NOT NULL,
    Team NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Type NVARCHAR(50) COLLATE Latin1_General_100_CI_AS_SC_UTF8 CHECK (Type IN ('Agent', 'Manager', 'Admin')),
    Activité NVARCHAR(100) COLLATE Latin1_General_100_CI_AS_SC_UTF8,
    Date_In DATE,
    CONSTRAINT PK_Effectifs_Hyp PRIMARY KEY (Hyp),
    CONSTRAINT FK_Effectifs_Users FOREIGN KEY (UserName) REFERENCES Users(UserName)
);

-- Index pour optimiser les recherches par UserName et Team
CREATE INDEX IX_Effectifs_UserName ON Effectifs(UserName);
CREATE INDEX IX_Effectifs_Team ON Effectifs(Team);

