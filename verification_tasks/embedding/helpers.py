import time
from tqdm import tqdm

def delete_entries_in_collection(collection, ids=None, batch_size=100):
    """
    Deletes entries in the specified collection by their IDs.
    If ids is None, deletes all entries in the collection.
    
    Args:
        collection: The collection from which to delete entries.
        ids: List of IDs to delete. If None, deletes all entries.
        batch_size: Number of entries to delete in a single batch.
    """
    if ids is None:
        # Delete all entries in the collection in batches
        try:
            count = collection.count()
            if count == 0:
                print("Collection is already empty.")
                return 0
            
            deleted_count = 0
            
            # Process in batches to avoid memory issues
            for i in tqdm(range(0, count, batch_size), desc="Delete Entries from Collection"):
                batch_ids = collection.get(limit=batch_size, offset=0)["ids"]
                if not batch_ids:
                    break
                    
                collection.delete(ids=[str(b_id) for b_id in batch_ids])
                deleted_count += len(batch_ids)
                time.sleep(0.1)  # Small delay to avoid overloading
                
            return deleted_count
        except Exception as e:
            print(f"Error deleting all entries: {str(e)}")
            return 0
    else:
        # Delete specific entries by ID
        ids = [str(id) for id in ids]  # Ensure IDs are strings
        deleted_count = 0
        try:
            for i in tqdm(range(0, len(ids), batch_size), desc="Delete Entries from Collection"):
                batch_ids = ids[i:i+batch_size]
                collection.delete(ids=batch_ids)
                deleted_count += len(batch_ids)
            
            
            print(f"Successfully deleted {deleted_count}/{len(ids)} entries from the collection.")
            return deleted_count
        except Exception as e:
            print(f"Error deleting entries: {str(e)}")
            return 0


def transfer_entries(source_collection, target_collection, ids, batch_size=100):
    """
    Transfers entries with specified IDs from source collection to target collection.
    
    Args:
        source_collection: The source collection to transfer from.
        target_collection: The target collection to transfer to.
        ids: List of IDs to transfer.
        batch_size: Number of entries to process in a single batch.
    """
    if not ids:
        print("No IDs provided for transfer.")
        return 0
    
    ids = [str(id) for id in ids]  # Ensure IDs are strings
    
    # First, check which IDs already exist in target collection (batch check)
    try:
        existing_check = target_collection.get(ids=ids, include=[])
        existing_ids = set(existing_check["ids"])
        ids_to_transfer = [id for id in ids if id not in existing_ids]
    except Exception as e:
        print(f"Warning: Could not check existing IDs: {e}")
        ids_to_transfer = ids
    
    if not ids_to_transfer:
        print("All entries already exist in target collection.")
        return 0
    
    print(f"Transferring {len(ids_to_transfer)} entries (skipping {len(ids) - len(ids_to_transfer)} existing)")
    
    total_transferred = 0
    failed_transfers = []
    
    # Process in batches
    for i in tqdm(range(0, len(ids_to_transfer), batch_size), desc="Transferring entries"):
        batch_ids = ids_to_transfer[i:i+batch_size]
        
        try:
            # Get batch from source collection
            source_entries = source_collection.get(
                ids=batch_ids,
                include=["embeddings", "documents", "metadatas"]
            )
            
            # Skip if no entries found
            if len(source_entries["ids"]) != len(batch_ids):
                failed_transfers.extend(batch_ids)
                continue
            
            # Batch transfer to target collection using upsert for safety
            target_collection.upsert(
                ids=source_entries["ids"],
                embeddings=source_entries["embeddings"],
                documents=source_entries["documents"],
                metadatas=source_entries["metadatas"]
            )
            
            total_transferred += len(source_entries["ids"])
            
        except Exception as e:
            print(f"Error in batch {i//batch_size + 1}: {str(e)}")
            failed_transfers.extend(batch_ids)
            
            # Fallback: try individual transfers for this batch
            individual_success = _transfer_batch_individually(
                source_collection, target_collection, batch_ids
            )
            total_transferred += individual_success
    
    # Report results
    if failed_transfers:
        print(f"Failed to transfer {len(failed_transfers)} entries")
        if len(failed_transfers) <= 10:  # Only show if not too many
            print(f"Failed IDs: {failed_transfers}")
    
    print(f"Successfully transferred {total_transferred} entries")
    return total_transferred


def _transfer_batch_individually(source_collection, target_collection, batch_ids):
    """
    Fallback function to transfer entries one by one when batch transfer fails.
    """
    success_count = 0
    
    for entry_id in batch_ids:
        try:
            # Get individual entry
            source_entry = source_collection.get(
                ids=[entry_id],
                include=["embeddings", "documents", "metadatas"]
            )
            
            if not source_entry["ids"]:
                continue
            
            # Transfer individual entry
            target_collection.upsert(
                ids=source_entry["ids"],
                embeddings=source_entry["embeddings"],
                documents=source_entry["documents"],
                metadatas=source_entry["metadatas"]
            )
            
            success_count += 1
            
        except Exception as e:
            print(f"Failed to transfer individual entry {entry_id}: {str(e)}")
    
    return success_count
