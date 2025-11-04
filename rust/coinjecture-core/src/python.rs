//! PyO3 bindings for Python interoperability.
//!
//! Exposes Rust functions to Python as native extension module.
//! All functions handle errors gracefully and return PyResult.

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use pyo3::exceptions::PyValueError;
use std::collections::HashMap;

use crate::codec::*;
use crate::commitment::*;
use crate::errors::ConsensusError;
use crate::hash::*;
use crate::merkle::*;
use crate::types::*;
use crate::verify::*;

/// Convert Rust Result to PyResult
fn to_py_result<T>(result: crate::Result<T>) -> PyResult<T> {
    result.map_err(|e| PyValueError::new_err(format!("{}", e)))
}

// ==================== HASHING FUNCTIONS ====================

/// Compute SHA-256 hash of bytes
#[pyfunction]
fn sha256_hash(py: Python, data: &[u8]) -> PyResult<PyObject> {
    let hash = sha256(data);
    Ok(PyBytes::new(py, &hash).into())
}

/// Compute double SHA-256 hash
#[pyfunction]
fn double_sha256_hash(py: Python, data: &[u8]) -> PyResult<PyObject> {
    let hash = double_sha256(data);
    Ok(PyBytes::new(py, &hash).into())
}

/// Derive address from public key
#[pyfunction]
fn derive_address_from_pubkey(py: Python, pubkey: &[u8]) -> PyResult<PyObject> {
    if pubkey.len() != 32 {
        return Err(PyValueError::new_err("Public key must be 32 bytes"));
    }
    let mut pubkey_arr = [0u8; 32];
    pubkey_arr.copy_from_slice(pubkey);
    let address = derive_address(&pubkey_arr);
    Ok(PyBytes::new(py, &address).into())
}

/// Compute epoch salt
#[pyfunction]
fn compute_epoch_salt_py(py: Python, parent_hash: &[u8], block_index: u64) -> PyResult<PyObject> {
    if parent_hash.len() != 32 {
        return Err(PyValueError::new_err("Parent hash must be 32 bytes"));
    }
    let mut parent = [0u8; 32];
    parent.copy_from_slice(parent_hash);
    let salt = compute_epoch_salt(&parent, block_index);
    Ok(PyBytes::new(py, &salt).into())
}

// ==================== CODEC FUNCTIONS ====================

/// Compute header hash from dict
#[pyfunction]
fn compute_header_hash_py(py: Python, header_dict: &PyDict) -> PyResult<PyObject> {
    let header = dict_to_header(header_dict)?;
    let hash = to_py_result(compute_header_hash(&header))?;
    Ok(PyBytes::new(py, &hash).into())
}

/// Encode block to bytes
#[pyfunction]
fn encode_block_py(py: Python, block_dict: &PyDict) -> PyResult<PyObject> {
    let block = dict_to_block(block_dict)?;
    let bytes = to_py_result(encode_block(&block))?;
    Ok(PyBytes::new(py, &bytes).into())
}

/// Decode block from bytes
#[pyfunction]
fn decode_block_py(bytes: &[u8]) -> PyResult<PyObject> {
    let block = to_py_result(decode_block(bytes))?;
    Python::with_gil(|py| block_to_dict(py, &block))
}

/// Encode transaction to bytes
#[pyfunction]
fn encode_transaction_py(py: Python, tx_dict: &PyDict) -> PyResult<PyObject> {
    let tx = dict_to_transaction(tx_dict)?;
    let bytes = to_py_result(encode_transaction(&tx))?;
    Ok(PyBytes::new(py, &bytes).into())
}

/// Compute transaction hash
#[pyfunction]
fn compute_transaction_hash_py(py: Python, tx_dict: &PyDict) -> PyResult<PyObject> {
    let tx = dict_to_transaction(tx_dict)?;
    let hash = to_py_result(compute_transaction_hash(&tx))?;
    Ok(PyBytes::new(py, &hash).into())
}

// ==================== MERKLE FUNCTIONS ====================

/// Compute Merkle root from transaction hashes
#[pyfunction]
fn compute_merkle_root_py(py: Python, tx_hashes: Vec<&[u8]>) -> PyResult<PyObject> {
    let hashes: Result<Vec<[u8; 32]>, _> = tx_hashes
        .iter()
        .map(|h| {
            if h.len() != 32 {
                Err(PyValueError::new_err("Transaction hash must be 32 bytes"))
            } else {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(h);
                Ok(arr)
            }
        })
        .collect();

    let hashes = hashes?;
    let root = compute_merkle_root(&hashes);
    Ok(PyBytes::new(py, &root).into())
}

// ==================== VERIFICATION FUNCTIONS ====================

/// Verify subset sum solution
#[pyfunction]
fn verify_subset_sum_py(
    problem_dict: &PyDict,
    solution_dict: &PyDict,
    budget_dict: &PyDict,
) -> PyResult<bool> {
    let problem = dict_to_problem(problem_dict)?;
    let solution = dict_to_solution(solution_dict)?;
    let budget = dict_to_budget(budget_dict)?;

    let result = to_py_result(verify_solution(&problem, &solution, &budget))?;
    Ok(result.valid)
}

// ==================== COMMITMENT FUNCTIONS ====================

/// Compute miner salt
#[pyfunction]
fn compute_miner_salt_py(
    py: Python,
    priv_key: &[u8],
    epoch_salt: &[u8],
    parent_hash: &[u8],
    block_index: u64,
) -> PyResult<PyObject> {
    if priv_key.len() != 32 || epoch_salt.len() != 32 || parent_hash.len() != 32 {
        return Err(PyValueError::new_err("All hashes must be 32 bytes"));
    }

    let mut priv_arr = [0u8; 32];
    let mut epoch_arr = [0u8; 32];
    let mut parent_arr = [0u8; 32];

    priv_arr.copy_from_slice(priv_key);
    epoch_arr.copy_from_slice(epoch_salt);
    parent_arr.copy_from_slice(parent_hash);

    let salt = to_py_result(compute_miner_salt(
        &priv_arr,
        &epoch_arr,
        &parent_arr,
        block_index,
    ))?;

    Ok(PyBytes::new(py, &salt).into())
}

// ==================== HELPER CONVERSIONS ====================

fn dict_to_header(dict: &PyDict) -> PyResult<BlockHeader> {
    Ok(BlockHeader {
        codec_version: dict.get_item("codec_version")?.unwrap().extract()?,
        block_index: dict.get_item("block_index")?.unwrap().extract()?,
        timestamp: dict.get_item("timestamp")?.unwrap().extract()?,
        parent_hash: extract_hash(dict, "parent_hash")?,
        merkle_root: extract_hash(dict, "merkle_root")?,
        miner_address: extract_hash(dict, "miner_address")?,
        commitment: extract_hash(dict, "commitment")?,
        difficulty_target: dict.get_item("difficulty_target")?.unwrap().extract()?,
        nonce: dict.get_item("nonce")?.unwrap().extract()?,
        extra_data: dict
            .get_item("extra_data")?
            .unwrap()
            .extract::<&[u8]>()?
            .to_vec(),
    })
}

fn dict_to_transaction(dict: &PyDict) -> PyResult<Transaction> {
    let tx_type_val: u8 = dict.get_item("tx_type")?.unwrap().extract()?;
    let tx_type = match tx_type_val {
        1 => TxType::Transfer,
        2 => TxType::ProblemSubmission,
        3 => TxType::BountyPayment,
        _ => return Err(PyValueError::new_err("Invalid tx_type")),
    };

    Ok(Transaction {
        codec_version: dict.get_item("codec_version")?.unwrap().extract()?,
        tx_type,
        from: extract_hash(dict, "from")?,
        to: extract_hash(dict, "to")?,
        amount: dict.get_item("amount")?.unwrap().extract()?,
        nonce: dict.get_item("nonce")?.unwrap().extract()?,
        gas_limit: dict.get_item("gas_limit")?.unwrap().extract()?,
        gas_price: dict.get_item("gas_price")?.unwrap().extract()?,
        signature: extract_signature(dict, "signature")?,
        data: dict.get_item("data")?.unwrap().extract::<&[u8]>()?.to_vec(),
        timestamp: dict.get_item("timestamp")?.unwrap().extract()?,
    })
}

fn dict_to_problem(dict: &PyDict) -> PyResult<Problem> {
    let problem_type_val: u8 = dict.get_item("problem_type")?.unwrap().extract()?;
    let problem_type = ProblemType::from_u8(problem_type_val)
        .ok_or_else(|| PyValueError::new_err("Invalid problem_type"))?;

    let tier_val: u8 = dict.get_item("tier")?.unwrap().extract()?;
    let tier = HardwareTier::from_u8(tier_val)
        .ok_or_else(|| PyValueError::new_err("Invalid tier"))?;

    Ok(Problem {
        problem_type,
        tier,
        elements: dict.get_item("elements")?.unwrap().extract()?,
        target: dict.get_item("target")?.unwrap().extract()?,
        timestamp: dict.get_item("timestamp")?.unwrap().extract()?,
    })
}

fn dict_to_solution(dict: &PyDict) -> PyResult<Solution> {
    Ok(Solution {
        indices: dict.get_item("indices")?.unwrap().extract()?,
        timestamp: dict.get_item("timestamp")?.unwrap().extract()?,
    })
}

fn dict_to_budget(dict: &PyDict) -> PyResult<VerifyBudget> {
    Ok(VerifyBudget {
        max_ops: dict.get_item("max_ops")?.unwrap().extract()?,
        max_duration_ms: dict.get_item("max_duration_ms")?.unwrap().extract()?,
        max_memory_bytes: dict.get_item("max_memory_bytes")?.unwrap().extract()?,
    })
}

fn dict_to_block(_dict: &PyDict) -> PyResult<Block> {
    // Simplified - real implementation would parse all fields
    Err(PyValueError::new_err("Not implemented yet"))
}

fn block_to_dict(_py: Python, _block: &Block) -> PyResult<PyObject> {
    // Simplified - real implementation would convert all fields
    Err(PyValueError::new_err("Not implemented yet"))
}

fn extract_hash(dict: &PyDict, key: &str) -> PyResult<[u8; 32]> {
    let bytes: &[u8] = dict.get_item(key)?.unwrap().extract()?;
    if bytes.len() != 32 {
        return Err(PyValueError::new_err(format!("{} must be 32 bytes", key)));
    }
    let mut arr = [0u8; 32];
    arr.copy_from_slice(bytes);
    Ok(arr)
}

fn extract_signature(dict: &PyDict, key: &str) -> PyResult<[u8; 64]> {
    let bytes: &[u8] = dict.get_item(key)?.unwrap().extract()?;
    if bytes.len() != 64 {
        return Err(PyValueError::new_err(format!("{} must be 64 bytes", key)));
    }
    let mut arr = [0u8; 64];
    arr.copy_from_slice(bytes);
    Ok(arr)
}

// ==================== MODULE DEFINITION ====================

/// COINjecture core consensus functions for Python
#[pymodule]
fn coinjecture_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sha256_hash, m)?)?;
    m.add_function(wrap_pyfunction!(double_sha256_hash, m)?)?;
    m.add_function(wrap_pyfunction!(derive_address_from_pubkey, m)?)?;
    m.add_function(wrap_pyfunction!(compute_epoch_salt_py, m)?)?;
    m.add_function(wrap_pyfunction!(compute_header_hash_py, m)?)?;
    m.add_function(wrap_pyfunction!(encode_block_py, m)?)?;
    m.add_function(wrap_pyfunction!(decode_block_py, m)?)?;
    m.add_function(wrap_pyfunction!(encode_transaction_py, m)?)?;
    m.add_function(wrap_pyfunction!(compute_transaction_hash_py, m)?)?;
    m.add_function(wrap_pyfunction!(compute_merkle_root_py, m)?)?;
    m.add_function(wrap_pyfunction!(verify_subset_sum_py, m)?)?;
    m.add_function(wrap_pyfunction!(compute_miner_salt_py, m)?)?;

    // Version info
    m.add("__version__", crate::VERSION)?;
    m.add("CODEC_VERSION", CODEC_VERSION)?;

    Ok(())
}
