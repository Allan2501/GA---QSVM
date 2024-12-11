import numpy as np
import qiskit
import random
from ..backend import constant
from .environment_parent import Metadata
from .environment_synthesis import MetadataSynthesis


def initialize_random_parameters(num_qubits: int, max_operands: int, conditional: bool, seed):
    if max_operands < 1 or max_operands > 3:
        raise qiskit.circuit.exceptions.CircuitError("max_operands must be between 1 and 3")

    qr = qiskit.circuit.QuantumRegister(num_qubits, 'q')
    qc = qiskit.circuit.QuantumCircuit(num_qubits)

    if conditional:
        cr = qiskit.circuit.ClassicalRegister(num_qubits, 'c')
        qc.add_register(cr)

    if seed is None:
        seed = np.random.randint(0, np.iinfo(np.int32).max) # Generate random number

    rng = np.random.default_rng(seed)  #Create random number generator
    thetas = qiskit.circuit.ParameterVector('theta')
    return qr, qc, rng, thetas
    
    
def choice_from_array(arr, condition):  # Choose an element from array that satisfies the condition
    item = None
    while item is None:
        item = random.choice(arr)
        if condition(item):
            return item
        else:
            item = None
    return item




def by_depth(metadata: Metadata) -> qiskit.QuantumCircuit:
    num_qubits = metadata.num_qubits
    depth = metadata.depth
    pool = [
        {'num_op': 1, 'operation': qiskit.circuit.library.RXGate, 'num_params': 1},
        {'num_op': 2, 'operation': qiskit.circuit.library.CXGate, 'num_params': 0}
    ]
    conditional = False
    seed = None
    max_operands = 2

    while True:  # Run while loop until satisfying the condition
        qr, qc, rng, thetas = initialize_random_parameters(num_qubits, max_operands, conditional, seed)
        thetas_length = 0
        while qc.depth() < depth:
            remaining_qubits = list(range(num_qubits))
            while remaining_qubits:
                max_possible_operands = min(len(remaining_qubits), max_operands)
                
                if max_possible_operands < 2:
                    num_operands = 1
                else:

                    num_operands = choice_from_array(
                        [1, 1, 1, 1, 1, 1, 2, 2, 2, 2], lambda value: value <= max_possible_operands)
                rng.shuffle(remaining_qubits)
                operands = remaining_qubits[:num_operands]
                remaining_qubits = [
                    q for q in remaining_qubits if q not in operands]
                num_op_pool = [
                    item for item in pool if item['num_op'] == num_operands]
                operation = rng.choice(num_op_pool)
                
                num_params = operation['num_params']
                thetas_length += num_params
                thetas.resize(thetas_length)
                angles = thetas[thetas_length - num_params:thetas_length]
                

                register_operands = [qr[i] for i in operands]
                op = operation['operation'](*angles) if num_params > 0 else operation['operation']()
            if qc.depth() >= depth:
                break
        if len(qc.parameters) == qc.num_qubits:
            break  

    return qc




def by_depth(metadata: Metadata) -> qiskit.QuantumCircuit:
    num_qubits = metadata.num_qubits
    depth = metadata.num_circuit  # Assuming depth corresponds to num_circuit
    pool = [
        {'num_op': 1, 'operation': qiskit.circuit.library.RXGate, 'num_params': 1},
        {'num_op': 2, 'operation': qiskit.circuit.library.CXGate, 'num_params': 0}
    ]
    conditional = False
    seed = None
    max_operands = 2

    while True:  # Lặp đến khi tìm được mạch thỏa mãn điều kiện
        qr, qc, rng, thetas = initialize_random_parameters(num_qubits, max_operands, conditional, seed)
        thetas_length = 0
        for _ in range(depth):
            remaining_qubits = list(range(num_qubits))
            while remaining_qubits:
                max_possible_operands = min(len(remaining_qubits), max_operands)
                num_operands = choice_from_array(
                    [1, 1, 1, 1, 1, 1, 2, 2, 2, 2], lambda value: value <= max_possible_operands)
                rng.shuffle(remaining_qubits)
                operands = remaining_qubits[:num_operands]
                remaining_qubits = [
                    q for q in remaining_qubits if q not in operands]
                num_op_pool = [
                    item for item in pool if item['num_op'] == num_operands]

                operation = rng.choice(num_op_pool)
                num_params = operation['num_params']
                thetas_length += num_params
                thetas.resize(thetas_length)
                angles = thetas[thetas_length - num_params:thetas_length]
                register_operands = [qr[i] for i in operands]
                op = operation['operation'](*angles) if num_params > 0 else operation['operation']()
                qc.append(op, register_operands)

        # Kiểm tra điều kiện: len(qc.parameters) == qc.num_qubits
        if len(qc.parameters) == qc.num_qubits:
            break  # Nếu điều kiện thỏa mãn, thoát vòng lặp

    return qc
    
    
    
    

def by_num_cnot_old(metadata: Metadata) -> qiskit.QuantumCircuit:
    num_qubits = metadata.num_qubits
    depth = metadata.depth
    pool = constant.operations_only_cnot
    conditional = False
    seed=None
    max_operands = 2
    qr, qc, rng, thetas = initialize_random_parameters(num_qubits, max_operands, conditional, seed)
    thetas_length = 0
    num_current_cnot = 0
    percent_cnot = 0.1 + 0.1 * np.random.randint(0, 3)
    for _ in range(depth):
        remaining_qubits = list(range(num_qubits))
        while remaining_qubits:
            max_possible_operands = min(len(remaining_qubits), max_operands)
            if num_current_cnot == metadata.num_cnot:
                max_possible_operands = 1
            else:
                if max_possible_operands == 2:
                    num_current_cnot += 1
            if max_possible_operands == 1:
                num_operands = 1
            else:
                num_operands = weighted_choice([1, 2], [1 - percent_cnot, percent_cnot])
            rng.shuffle(remaining_qubits)
            operands = remaining_qubits[:num_operands]
            remaining_qubits = [
                q for q in remaining_qubits if q not in operands]
            num_op_pool = [
                item for item in pool if item['num_op'] == num_operands]

            operation = rng.choice(num_op_pool)
            num_params = operation['num_params']
            thetas_length += num_params
            thetas.resize(thetas_length)
            angles = thetas[thetas_length - num_params:thetas_length]
            register_operands = [qr[i] for i in operands]
            op = operation['operation'](*angles)
            qc.append(op, register_operands)
    return qc