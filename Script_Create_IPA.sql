-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema IPA
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema IPA
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `IPA` DEFAULT CHARACTER SET utf8 ;
USE `IPA` ;

-- -----------------------------------------------------
-- Table `IPA`.`usuario`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`usuario` (
  `CPF` INT NOT NULL,
  `nome` VARCHAR(60) NOT NULL,
  `email` VARCHAR(60) NOT NULL,
  `senhaHash` VARCHAR(15) NOT NULL,
  `cargo` VARCHAR(45) NOT NULL,
  `dataCadastro` DATE NOT NULL,
  `tipoUsuario` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`CPF`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`Municipio`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`Municipio` (
  `idMunicipio` INT NOT NULL,
  `nome` VARCHAR(45) NOT NULL,
  `regiao` VARCHAR(45) NULL,
  PRIMARY KEY (`idMunicipio`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`Armazem`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`Armazem` (
  `idArmazem` INT NOT NULL,
  `nome` VARCHAR(45) NOT NULL,
  `capacidadeKg` INT NOT NULL,
  `Municipio_idMunicipio1` INT NOT NULL,
  PRIMARY KEY (`idArmazem`),
  UNIQUE INDEX `idArmazém_UNIQUE` (`idArmazem` ASC) VISIBLE,
  INDEX `fk_Armazem_Municipio_idx` (`Municipio_idMunicipio1` ASC) VISIBLE,
  CONSTRAINT `fk_Armazem_Municipio`
    FOREIGN KEY (`Municipio_idMunicipio1`)
    REFERENCES `IPA`.`Municipio` (`idMunicipio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`Semente`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`Semente` (
  `idSemente` INT NOT NULL,
  `tipo` VARCHAR(45) NOT NULL,
  `dataValidade` DATE NOT NULL,
  `safra` VARCHAR(45) NOT NULL,
  `observacao` VARCHAR(150) NOT NULL,
  `pesoTotalKg` INT NOT NULL,
  PRIMARY KEY (`idSemente`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`Lote`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`Lote` (
  `idLote` INT NOT NULL,
  `status` VARCHAR(45) NOT NULL,
  `dataEntrada` DATE NOT NULL,
  `dataSaida` DATE NULL,
  `quantidadeKg` INT NOT NULL,
  `Armazem_idArmazem` INT NOT NULL,
  `Semente_idSemente` INT NOT NULL,
  PRIMARY KEY (`idLote`),
  INDEX `fk_Lote_Armazem1_idx` (`Armazem_idArmazem` ASC) VISIBLE,
  INDEX `fk_Lote_Semente1_idx` (`Semente_idSemente` ASC) VISIBLE,
  CONSTRAINT `fk_Lote_Armazem1`
    FOREIGN KEY (`Armazem_idArmazem`)
    REFERENCES `IPA`.`Armazem` (`idArmazem`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Lote_Semente1`
    FOREIGN KEY (`Semente_idSemente`)
    REFERENCES `IPA`.`Semente` (`idSemente`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`Distribuicao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`Distribuicao` (
  `idDistribuicao` INT NOT NULL,
  `dataDistribuicao` DATE NOT NULL,
  `status` VARCHAR(45) NOT NULL,
  `Armazem_idArmazem_Origem` INT NOT NULL,
  `Armazem_idArmazem_Destino` INT NOT NULL,
  `usuario_CPF` INT NOT NULL,
  `Lote_idLote` INT NOT NULL,
  PRIMARY KEY (`idDistribuicao`),
  INDEX `fk_Distribuicao_Armazem1_idx` (`Armazem_idArmazem_Origem` ASC) VISIBLE,
  INDEX `fk_Distribuicao_Armazem2_idx` (`Armazem_idArmazem_Destino` ASC) VISIBLE,
  INDEX `fk_Distribuicao_usuario1_idx` (`usuario_CPF` ASC) VISIBLE,
  INDEX `fk_Distribuicao_Lote1_idx` (`Lote_idLote` ASC) VISIBLE,
  CONSTRAINT `fk_Distribuicao_Armazem1`
    FOREIGN KEY (`Armazem_idArmazem_Origem`)
    REFERENCES `IPA`.`Armazem` (`idArmazem`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Distribuicao_Armazem2`
    FOREIGN KEY (`Armazem_idArmazem_Destino`)
    REFERENCES `IPA`.`Armazem` (`idArmazem`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Distribuicao_usuario1`
    FOREIGN KEY (`usuario_CPF`)
    REFERENCES `IPA`.`usuario` (`CPF`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Distribuicao_Lote1`
    FOREIGN KEY (`Lote_idLote`)
    REFERENCES `IPA`.`Lote` (`idLote`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`relatorio`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`relatorio` (
  `idRelatorio` INT NOT NULL,
  `dataFim` DATE NOT NULL,
  `dataInicio` DATE NOT NULL,
  `tipo` VARCHAR(45) NOT NULL,
  `dataGeracao` DATE NOT NULL,
  `titulo` VARCHAR(60) NOT NULL,
  `aquivoPDF` VARCHAR(45) NOT NULL,
  `Distribuicao_idDistribuicao` INT NOT NULL,
  PRIMARY KEY (`idRelatorio`),
  INDEX `fk_relatorio_Distribuicao1_idx` (`Distribuicao_idDistribuicao` ASC) VISIBLE,
  CONSTRAINT `fk_relatorio_Distribuicao1`
    FOREIGN KEY (`Distribuicao_idDistribuicao`)
    REFERENCES `IPA`.`Distribuicao` (`idDistribuicao`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`Transparencia`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`Transparencia` (
  `idTransparencia` INT NOT NULL,
  `dataAtualizacao` VARCHAR(45) NOT NULL,
  `Distribuicao_idDistribuicao` INT NOT NULL,
  PRIMARY KEY (`idTransparencia`),
  INDEX `fk_Transparencia_Distribuicao1_idx` (`Distribuicao_idDistribuicao` ASC) VISIBLE,
  CONSTRAINT `fk_Transparencia_Distribuicao1`
    FOREIGN KEY (`Distribuicao_idDistribuicao`)
    REFERENCES `IPA`.`Distribuicao` (`idDistribuicao`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`Telefone`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`Telefone` (
  `telefone` INT NOT NULL,
  `usuario_CPF` INT NOT NULL,
  PRIMARY KEY (`telefone`),
  INDEX `fk_Telefone_usuario1_idx` (`usuario_CPF` ASC) VISIBLE,
  CONSTRAINT `fk_Telefone_usuario1`
    FOREIGN KEY (`usuario_CPF`)
    REFERENCES `IPA`.`usuario` (`CPF`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `IPA`.`endereco`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `IPA`.`endereco` (
  `CEP` INT NOT NULL,
  `Rua` VARCHAR(45) NOT NULL,
  `numero` INT NOT NULL,
  `Bairro` VARCHAR(45) NOT NULL,
  `Complemento` VARCHAR(100) NULL,
  `Armazem_idArmazem` INT NOT NULL,
  INDEX `fk_endereco_Armazem1_idx` (`Armazem_idArmazem` ASC) VISIBLE,
  CONSTRAINT `fk_endereco_Armazem1`
    FOREIGN KEY (`Armazem_idArmazem`)
    REFERENCES `IPA`.`Armazem` (`idArmazem`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
